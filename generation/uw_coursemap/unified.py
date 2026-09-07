"""One local-tool enrichment conversation, with independent section acceptance."""

import copy
import json
import os
import re
import time

import jsonschema
import requests

from .course_context import CourseLookup
from .jobs import WORKER_VERSION, generation_schema
from .models import digest
from .requirements import restore_quotes, validate_graph


SECTIONS = ("search_profile", "requirements", "student_experience")


def validate_section(name, candidate, task, root, lookup):
    jsonschema.Draft202012Validator(task["schema"]["properties"][name]).validate(
        candidate
    )
    value = copy.deepcopy(candidate)
    state = "valid"
    if name == "search_profile":
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
                course = lookup.evidence.get(citation["course_id"])
                if course is None or citation["quote"] not in course.get(
                    citation["field"], ""
                ):
                    raise ValueError(
                        "Search evidence must quote a supplied course field"
                    )
        for claim in [value["summary"], *value["topics"], *value["skills_taught"]]:
            if any(
                e["course_id"] != root["course_id"] or e["field"] != "description"
                for e in claim["evidence"]
            ):
                raise ValueError(
                    "Taught content must cite the root course description, not prerequisites"
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
    return {"status": state, "value": value, "error": None}


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
    # Three tool rounds, one mandatory final response, one targeted correction.
    for turn in range(5):
        allow_lookup = turn < 3 and lookup.calls < lookup.max_calls
        try:
            response, tokens = transport(profile, task, messages, allow_lookup)
        except (ValueError, requests.RequestException, KeyError, IndexError) as exc:
            attempts.append(
                {
                    "turn": turn,
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
                break  # Keep successful sections if a correction request fails.
            if turn == 4:
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
            attempts.append({"turn": turn, "error": "Expected an object"})
            continue
        calls = response.get("lookups", [])
        if not isinstance(calls, list):
            calls = []
        errors = {}
        for name in SECTIONS:
            if calls and allow_lookup:
                continue  # Accept claims only after requested evidence arrives.
            if name in sections and sections[name]["status"] != "invalid":
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
                errors[name] = reason[:600]
                sections[name] = {
                    "status": "invalid",
                    "value": None,
                    "candidate": candidate,
                    "error": reason[:600],
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
        attempts.append({"turn": turn, "errors": errors, "tool_results": results})
        if not results and any(response.get(name) is not None for name in SECTIONS):
            final_turns += 1
        missing = [
            name
            for name in SECTIONS
            if name not in sections or sections[name]["status"] == "invalid"
        ]
        if not missing or final_turns >= 2:
            break
        # Do not repeatedly echo large candidates; keep evidence and actionable errors.
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
                        "instruction": "Return missing sections. Already accepted sections must be null. Use lookups [] now."
                        if not allow_lookup or not results
                        else "Use returned evidence; finish sections when ready.",
                    },
                    ensure_ascii=False,
                ),
            }
        )
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
