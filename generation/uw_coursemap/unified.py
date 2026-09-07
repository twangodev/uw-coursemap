"""One local-tool enrichment conversation, with independent section acceptance."""

import copy
import json
import os
import re
import time

import jsonschema
import requests

from .course_context import CourseLookup, text_view
from .jobs import WORKER_VERSION, generation_schema
from .models import digest
from .requirements import graph_diagnostics, restore_quotes, validate_graph
from .requirements_eval import expression, normalize


SECTIONS = ("search_profile", "requirements", "student_experience")


def compare_parsers(section, original):
    def convert(node):
        if isinstance(node, str):
            if text_view(node).lower().rstrip(".") in {
                "",
                "none",
                "no prerequisites",
                "no requisites",
            }:
                return None
            return {"condition": text_view(node)}
        if isinstance(node, dict) and "course_number" in node:
            return {
                "course": {
                    "subjects": node["subjects"],
                    "course_number": node["course_number"],
                    "timing": "prior",
                    "minimum_grade": None,
                }
            }
        if isinstance(node, dict) and node.get("operator") in {"AND", "OR", "NOT"}:
            return {
                {"AND": "all", "OR": "any", "NOT": "not"}[node["operator"]]: [
                    convert(c) for c in node["children"]
                ]
            }
        raise ValueError("Unsupported legacy AST form")

    comparison = {
        "structural_match": None,
        "note": "Both parsers are candidates; structural agreement does not prove semantic correctness.",
    }
    if original.get("ast") is not None and section.get("value") is not None:
        try:
            comparison["structural_match"] = normalize(
                convert(original["ast"])
            ) == normalize(expression(section["value"]))
        except (ValueError, KeyError, TypeError, IndexError):
            comparison["note"] = (
                "Legacy AST could not be compared; preserve both candidates for review."
            )
        if comparison["structural_match"] is False and section["status"] == "valid":
            section["status"] = "needs_review"
    section["parser_comparison"] = comparison


def quote_projection(text):
    chars, positions = [], []
    for i, char in enumerate(text):
        char = {"’": "'", "‘": "'", "“": '"', "”": '"'}.get(char, char)
        if char == '"' or (
            char == "'"
            and not (
                i > 0
                and i + 1 < len(text)
                and text[i - 1].isalnum()
                and text[i + 1].isalnum()
            )
        ):
            continue
        chars.append(char)
        positions.append(i)
    return "".join(chars), positions


def literal_span(quote, source):
    position = source.find(quote)
    if position >= 0:
        return position, position + len(quote)
    projected, positions = quote_projection(source)
    needle, _ = quote_projection(quote)
    position = projected.find(needle) if needle else -1
    if position >= 0:
        return positions[position], positions[position + len(needle) - 1] + 1
    return None


def source_quote(quote, source):
    if quote in source:
        return quote
    quote = text_view(quote)
    span = literal_span(quote, source)
    if span is not None:
        return source[span[0] : span[1]]
    parts = [part.strip() for part in re.split(r"\.{3}|…", quote) if part.strip()]
    if len(parts) < 2:
        return None
    start, end = None, 0
    for part in parts:
        span = literal_span(part, source[end:])
        if span is None:
            return None
        if start is None:
            start = end + span[0]
        end += span[1]
    return source[start:end]


def excluded_background(course, root):
    ref = course["course_reference"]
    for clause in re.findall(r"Not open[^.!?]*", root["requirements_text"], re.I):
        compact = re.sub(r"[^A-Z0-9]", "", clause.upper())
        if re.search(
            r"(?<!\d)" + str(ref["course_number"]) + r"(?!\d)", clause
        ) and any(
            re.sub(r"[^A-Z0-9]", "", subject.upper()) in compact
            for subject in ref["subjects"]
        ):
            return True
    return False


def validate_section(name, candidate, task, root, lookup):
    jsonschema.Draft202012Validator(task["schema"]["properties"][name]).validate(
        candidate
    )
    value = copy.deepcopy(candidate)
    state = "valid"
    repairs = []
    if name == "search_profile":
        summary = value["summary"]["text"].rstrip()
        if summary.endswith((",", ";", ":")):
            raise ValueError(
                "Summary appears clipped; rewrite it as a short complete sentence, never cut a word or end with a comma."
            )
        claims = [
            value["summary"],
            *value["topics"],
            *value["skills_taught"],
            *value["assumed_background"],
        ]
        for claim in claims:
            if not claim["evidence"]:
                raise ValueError("Search claims require evidence")
            for citation in claim["evidence"]:
                original = copy.deepcopy(citation)
                key = lookup.context.resolve(citation["course_id"])
                course = lookup.evidence.get(key)
                quote = (
                    source_quote(citation["quote"], course.get(citation["field"], ""))
                    if course
                    else None
                )
                if not quote and course and citation["field"] == "description":
                    quote = source_quote(citation["quote"], course.get("title", ""))
                    if quote:
                        citation["field"] = "title"
                if not quote:
                    raise ValueError(
                        f"Invalid evidence for {citation['course_id']}.{citation['field']}: {citation['quote']!r}. Copy a short exact substring from supplied text; do not paraphrase or invent omitted text."
                    )
                citation.update(course_id=key, quote=quote)
                if citation != original:
                    repairs.append(
                        {"original": original, "resolved": copy.deepcopy(citation)}
                    )
        for claim in [value["summary"], *value["topics"], *value["skills_taught"]]:
            if any(
                e["course_id"] != root["course_id"]
                or e["field"] not in {"description", "title"}
                for e in claim["evidence"]
            ):
                raise ValueError(
                    "Taught content must cite the root course description or title, not prerequisites. Omit claims supported only by another course."
                )
        for claim in value["assumed_background"]:
            for citation in claim["evidence"]:
                key = citation["course_id"]
                if key != root["course_id"] and excluded_background(
                    lookup.evidence[key], root
                ):
                    raise ValueError(
                        f"{key} is listed in a credit exclusion, not a positive prerequisite. Remove background claims imported from this excluded course; do not relabel taught content as assumed knowledge."
                    )
        jsonschema.Draft202012Validator(task["schema"]["properties"][name]).validate(
            value
        )
    elif name == "requirements":
        linked = list(root["linked_courses"])
        compact = re.sub(r"[^A-Z0-9]", "", root["requirements_text"].upper())
        for key, course in lookup.evidence.items():
            ref = course["course_reference"]
            number = str(ref["course_number"])
            if (
                key != root["course_id"]
                and re.search(
                    r"(?<!\d)" + number + r"(?!\d)", root["requirements_text"]
                )
                and any(re.sub(r"[^A-Z0-9]", "", s) in compact for s in ref["subjects"])
            ):
                if ref not in linked:
                    linked.append(ref)
        payload = {
            "requirements_text": root["requirements_text"],
            "linked_courses": linked,
        }
        restore_quotes(value, payload)
        diagnostics = graph_diagnostics(value, payload)
        if diagnostics:
            raise ValueError("\n".join(diagnostics))
        validate_graph(value, payload)
        state = "needs_review" if value["status"] == "needs_review" else "valid"
    else:
        reviews = {r["id"]: r for r in root["reviews"]}
        if value["status"] == "insufficient_evidence":
            if value["themes"]:
                raise ValueError(
                    "Insufficient evidence cannot contain sentiment claims"
                )
            state = "insufficient_evidence"
        else:
            if not reviews or not value["themes"]:
                raise ValueError(
                    "Supported sentiment requires attributable reviews and themes"
                )
            for theme in value["themes"]:
                ids = theme["review_ids"]
                if (
                    not ids
                    or len(set(ids)) != len(ids)
                    or any(key not in reviews for key in ids)
                ):
                    raise ValueError(
                        "Sentiment cites unavailable or duplicate review evidence"
                    )
                theme["evidence_count"] = len(ids)
                theme["evidence"] = [reviews[key] for key in ids]
    return {"status": state, "value": value, "error": None, "citation_repairs": repairs}


def request(profile, task, messages, allow_lookup):
    properties = {}
    properties["lookups"] = {
        "type": "array",
        "maxItems": 6 if allow_lookup else 0,
        "items": {
            "type": "object",
            "additionalProperties": False,
            "required": ["course_id", "from_course"],
            "properties": {
                "course_id": {"type": "string", "minLength": 1, "maxLength": 100},
                "from_course": {"type": "string", "minLength": 1, "maxLength": 100},
            },
        },
    }
    if len(messages) > 2:
        properties.update(
            {
                name: {"anyOf": [task["schema"]["properties"][name], {"type": "null"}]}
                for name in SECTIONS
            }
        )
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": list(properties),
        "properties": properties,
    }
    headers = {}
    if os.environ.get("COURSEMAP_INFERENCE_API_KEY"):
        headers["Authorization"] = "Bearer " + os.environ["COURSEMAP_INFERENCE_API_KEY"]
    for attempt in range(3):
        try:
            response = requests.post(
                profile["base_url"].rstrip("/") + "/chat/completions",
                headers=headers,
                json={
                    "model": f"{profile['model']}@{profile['revision']}",
                    "messages": messages,
                    "temperature": profile["temperature"],
                    "max_tokens": min(1024, profile["max_output_tokens"])
                    if len(messages) == 2
                    else profile["max_output_tokens"],
                    "chat_template_kwargs": {"enable_thinking": profile["thinking"]},
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "course_enrichment_turn",
                            "strict": True,
                            "schema": generation_schema(schema),
                        },
                    },
                },
                timeout=(10, profile.get("request_timeout_seconds", 180)),
            )
            if response.status_code in {429, 500, 502, 503, 504} and attempt < 2:
                time.sleep(2**attempt)
                continue
            response.raise_for_status()
            data = response.json()
            if data.get("model") != f"{profile['model']}@{profile['revision']}":
                raise ValueError("Server returned a different model identity")
            choice = data["choices"][0]
            if choice["finish_reason"] != "stop":
                raise ValueError(
                    "Unified output was truncated; increase the output budget"
                )
            return json.loads(choice["message"]["content"]), data.get("usage", {})
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(2**attempt)


def generate_unified(profile, task, payload, context, transport=request):
    root = payload
    repair_limit = task.get("ast_repair_attempts", 2)
    if type(repair_limit) is not int or repair_limit not in {0, 1, 2}:
        raise ValueError("ast_repair_attempts must be 0, 1, or 2")
    lookup = CourseLookup(context, root["course_id"], **task.get("tool_limits", {}))
    view = {k: v for k, v in root.items() if k != "original_requirements"}
    messages = [
        {
            "role": "system",
            "content": task["prompt"]
            + "\nFinal section schemas:\n"
            + json.dumps(task["schema"], ensure_ascii=False),
        },
        {"role": "user", "content": json.dumps(view, ensure_ascii=False)},
    ]
    sections = {}
    attempts = []
    final_turns = 0
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    repair_message = None
    repair_attempts = 0
    # Three tool rounds, one final response, at most two correction attempts.
    for turn in range(6):
        repairing = (
            repair_attempts < repair_limit
            and sections.get("requirements", {}).get("status") == "invalid"
        )
        turn_profile = {**profile, "thinking": True} if repairing else profile
        if repairing:
            repair_attempts += 1
        allow_lookup = not sections and turn < 3 and lookup.calls < lookup.max_calls
        try:
            response, tokens = transport(turn_profile, task, messages, allow_lookup)
        except (ValueError, requests.RequestException, KeyError, IndexError) as exc:
            attempts.append(
                {
                    "turn": turn,
                    "thinking": turn_profile.get("thinking", False),
                    "error": type(exc).__name__
                    + ": "
                    + (
                        str(exc)[:600]
                        if isinstance(exc, ValueError)
                        else "Inference request failed"
                    ),
                }
            )
            if sections:
                if not repairing or repair_attempts >= repair_limit and repairing:
                    break
                continue  # Retry the same rejected AST once; retain accepted sections.
            if turn == 5:
                raise
            messages.append(
                {
                    "role": "user",
                    "content": "Return a complete JSON object within the output limit. Use short notes and omit optional claims.",
                }
            )
            continue
        for key in usage:
            usage[key] += tokens.get(key, 0)
        if not isinstance(response, dict):
            attempts.append(
                {
                    "turn": turn,
                    "thinking": turn_profile.get("thinking", False),
                    "error": "Expected an object",
                }
            )
            if repair_attempts >= repair_limit and repairing:
                break
            continue
        calls = response.get("lookups", [])
        if not isinstance(calls, list):
            calls = []
        errors = {}
        for name in SECTIONS:
            if calls and allow_lookup:
                continue  # Accept claims only after requested evidence arrives.
            if name in sections and (
                sections[name]["status"] != "invalid"
                or (name == "requirements" and repair_limit == 0)
            ):
                continue
            candidate = response.get(name)
            if candidate is None:
                continue
            try:
                sections[name] = validate_section(name, candidate, task, root, lookup)
            except (ValueError, KeyError, TypeError, jsonschema.ValidationError) as exc:
                reason = (
                    exc.message
                    if isinstance(exc, jsonschema.ValidationError)
                    else str(exc)
                )
                errors[name] = reason[:6000]
                sections[name] = {
                    "status": "invalid",
                    "value": None,
                    "candidate": candidate,
                    "error": reason[:6000],
                }
        results = []
        if allow_lookup:
            for call in calls[:6]:
                if isinstance(call, dict) and all(
                    isinstance(call.get(k), str) for k in ["course_id", "from_course"]
                ):
                    results.append(
                        lookup.get_course(call["course_id"], call["from_course"])
                    )
        attempts.append(
            {
                "turn": turn,
                "thinking": turn_profile.get("thinking", False),
                "errors": errors,
                "tool_results": results,
                "rejected_requirements": sections.get("requirements", {}).get(
                    "candidate"
                )
                if "requirements" in errors
                else None,
            }
        )
        if not results and any(response.get(name) is not None for name in SECTIONS):
            final_turns += 1
        missing = [
            name
            for name in SECTIONS
            if name not in sections
            or (
                sections[name]["status"] == "invalid"
                and not (name == "requirements" and repair_attempts >= repair_limit)
            )
        ]
        if (
            not missing
            or final_turns >= 3
            or repair_attempts >= repair_limit
            and repairing
        ):
            break
        # Keep only the latest repair candidate to bound context growth.
        if repair_message is not None:
            messages.remove(repair_message)
        messages.append(
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "tool_results": results,
                        "accepted_sections": [
                            name
                            for name in sections
                            if sections[name]["status"] != "invalid"
                        ],
                        "sections_needed": missing,
                        "validation_errors": errors,
                        "rejected_requirements": sections.get("requirements", {}).get(
                            "candidate"
                        )
                        if "requirements" in missing
                        else None,
                        "deferred_sections": ["requirements"]
                        if "requirements" in sections
                        and sections["requirements"]["status"] == "invalid"
                        and "requirements" not in missing
                        else [],
                        "instruction": "Return only sections_needed. Accepted and deferred sections must be null. Use lookups [] now."
                        if not allow_lookup or not results
                        else "Use returned evidence; finish sections when ready.",
                    },
                    ensure_ascii=False,
                ),
            }
        )
        repair_message = messages[-1] if sections else None
    for name in SECTIONS:
        if name not in sections:
            sections[name] = {
                "status": "insufficient_evidence"
                if name == "student_experience" and not root["reviews"]
                else "invalid",
                "value": {"status": "insufficient_evidence", "themes": []}
                if name == "student_experience" and not root["reviews"]
                else None,
                "error": None
                if name == "student_experience" and not root["reviews"]
                else "Model did not return this section",
            }
    compare_parsers(sections["requirements"], root["original_requirements"])
    return {
        "course_id": root["course_id"],
        "model": profile["model"],
        "model_revision": profile["revision"],
        "model_id": f"{profile['model']}@{profile['revision']}",
        "task_version": task["version"],
        "sections": sections,
        "source_requirements": root["original_requirements"],
        "course_history": root["history"],
        "provenance": {
            "worker_version": WORKER_VERSION,
            "ast_repair_attempts": repair_limit,
            "generation_settings": {
                key: profile[key]
                for key in (
                    "temperature",
                    "thinking",
                    "max_output_tokens",
                    "context_length",
                    "engine",
                    "engine_version",
                )
                if key in profile
            },
            "input_hash": digest(root),
            "task_hash": digest(task),
            "dependencies": lookup.dependencies,
            "tool_calls": lookup.trace,
            "attempts": attempts,
            "review_coverage": {"attributable_reviews": len(root["reviews"])},
        },
    }, usage
