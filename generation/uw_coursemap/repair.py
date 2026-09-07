"""Checkpointed repair jobs using native assistant/validator conversation turns."""

import copy
import json

import jsonschema
import requests

from .course_context import CourseLookup
from .models import canonical, digest
from .profiles import load_profile
from .store import now
from .unified import SECTIONS, compare_parsers, request, validate_section


def create_repair(
    jobs, parent_id, profiles, profile_name, limit=20, course_ids=None, turns=3
):
    from .jobs import WORKER_VERSION

    if limit < 0 or not 1 <= turns <= 4:
        raise ValueError("limit must be nonnegative and turns must be between 1 and 4")
    parent = jobs.status(parent_id)
    if parent["status"] != "complete":
        raise ValueError("Repair requires a completed parent job")
    original = json.loads(parent["spec_json"])
    if original["task"].get("workflow") != "unified_v1":
        raise ValueError("Repair requires unified course enrichment")
    profile = load_profile(profiles, profile_name)
    if profile.runner != "generate" or (profile.model, profile.revision) != (
        original["profile"]["model"],
        original["profile"]["revision"],
    ):
        raise ValueError(
            "Repair must use the same pinned generation model to retain accepted sections"
        )
    profile.thinking = True
    rows = []
    for row in jobs.db.execute(
        "SELECT * FROM results WHERE job_id=? ORDER BY course_id", (parent_id,)
    ):
        output = json.loads(row["output_json"])
        if any(
            section.get("status") == "invalid"
            for section in output.get("sections", {}).values()
        ):
            rows.append(dict(row))
    if course_ids:
        requested = set(course_ids)
        rows = [row for row in rows if row["course_id"] in requested]
        if {row["course_id"] for row in rows} != requested:
            raise ValueError(
                "Each requested canonical course ID must have a rejected section"
            )
    rows.sort(key=lambda row: digest(row["course_id"]))
    if limit:
        rows = rows[:limit]
    if not rows:
        raise ValueError("No rejected course sections selected")
    task = {**original["task"], "repair_mode": "conversation_v1", "repair_turns": turns}
    spec = {
        **original,
        "task": task,
        "profile": profile.model_dump(),
        "worker_version": WORKER_VERSION,
        "selected_courses": len(rows),
        "repair_parent": parent_id,
        "repair_parent_results_hash": digest(
            [(r["course_id"], r["output_json"]) for r in rows]
        ),
    }
    job = "enrich-" + digest({"source_run": parent["source_run"], "spec": spec})[:24]
    with jobs.db:
        jobs.db.execute(
            "INSERT OR IGNORE INTO jobs VALUES(?,?,?,'pending',?)",
            (job, parent["source_run"], canonical(spec), now()),
        )
        for row in rows:
            payload = json.loads(row["input_json"])
            # For chained repair jobs, replace the seed rather than nesting it.
            payload["repair_seed"] = {
                "job_id": parent_id,
                "output": json.loads(row["output_json"]),
            }
            cache_key = digest(
                {
                    "input": payload,
                    "task": task,
                    "profile": profile.model_dump(exclude={"base_url", "concurrency"}),
                    "worker_version": WORKER_VERSION,
                }
            )
            jobs.db.execute(
                "INSERT OR IGNORE INTO results(job_id,course_id,cache_key,input_json,status) VALUES(?,?,?,?,'pending')",
                (job, row["course_id"], cache_key, canonical(payload)),
            )
    return job


def generate_repair(profile, task, payload, context, transport=request):
    seed = payload["repair_seed"]
    previous = seed["output"]
    root = {key: value for key, value in payload.items() if key != "repair_seed"}
    if context.fingerprint(root["course_id"]) != digest(root):
        raise ValueError("Repair source context changed")
    lookup = CourseLookup(context, root["course_id"], **task.get("tool_limits", {}))
    for key, stamp in previous.get("provenance", {}).get("dependencies", {}).items():
        if context.fingerprint(key) != stamp:
            raise ValueError("Repair dependency changed")
    # Replay only previously permitted local lookups, against the same snapshot.
    for call in previous.get("provenance", {}).get("tool_calls", []):
        if call.get("tool") == "get_course":
            lookup.get_course(call["course_id"], call["from_course"])
    sections = copy.deepcopy(previous["sections"])
    targets = [name for name in SECTIONS if sections[name]["status"] == "invalid"]
    locked = [name for name in SECTIONS if name not in targets]
    initial = {
        name: sections[name].get("candidate") if name in targets else None
        for name in SECTIONS
    }
    initial["lookups"] = []
    messages = [
        {
            "role": "system",
            "content": task["prompt"]
            + "\nRepair rejected sections only. Preserve all source conditions, including exclusions. Return null for locked sections and lookups []. Treat prior answers as candidates, not facts.\nSection schemas:\n"
            + canonical(task["schema"]),
        },
        {
            "role": "user",
            "content": canonical(
                {
                    "course": {
                        k: v
                        for k, v in root.items()
                        if k not in {"original_requirements", "history"}
                    },
                    "lookup_evidence": {
                        k: v
                        for k, v in lookup.evidence.items()
                        if k != root["course_id"]
                    },
                    "locked_sections": locked,
                }
            ),
        },
        {"role": "assistant", "content": canonical(initial)},
    ]
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    attempts = []
    repaired = set()
    transport_error = None
    for turn in range(task["repair_turns"]):
        needed = [name for name in targets if sections[name]["status"] == "invalid"]
        if not needed:
            break
        feedback = {
            "sections_needed": needed,
            "locked_sections": [name for name in SECTIONS if name not in needed],
            "validation_errors": {name: sections[name].get("error") for name in needed},
            "instruction": "Correct the previous assistant answer using the source. Return only sections_needed; other sections must be null. Use lookups [].",
        }
        if transport_error:
            feedback["previous_request_error"] = transport_error
        messages.append({"role": "user", "content": canonical(feedback)})
        try:
            response, tokens = transport(
                {**profile, "thinking": True}, task, messages, False
            )
            for key in usage:
                usage[key] += tokens.get(key, 0)
            if not isinstance(response, dict):
                raise ValueError("Expected an object")
        except (ValueError, requests.RequestException, KeyError, IndexError) as exc:
            transport_error = (
                str(exc)[:1000]
                if isinstance(exc, ValueError)
                else "Inference request failed"
            )
            attempts.append({"turn": turn, "thinking": True, "error": transport_error})
            # No assistant answer arrived; keep a single feedback turn for retry.
            messages.pop()
            continue
        transport_error = None
        messages.append({"role": "assistant", "content": canonical(response)})
        errors = {}
        for name in needed:
            candidate = response.get(name)
            if candidate is None:
                errors[name] = "Required repair section was omitted"
                sections[name]["error"] = errors[name]
                continue
            try:
                sections[name] = validate_section(name, candidate, task, root, lookup)
                if name == "requirements":
                    compare_parsers(sections[name], root["original_requirements"])
                repaired.add(name)
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
                    "error": errors[name],
                }
        attempts.append({"turn": turn, "thinking": True, "errors": errors})
    result = copy.deepcopy(previous)
    result["sections"] = sections
    result["provenance"] = {
        "worker_version": previous["provenance"]["worker_version"],
        "repair_version": 1,
        "repair_parent_job": seed["job_id"],
        "repair_parent_output_hash": digest(previous),
        "retained_sections": locked,
        "repaired_sections": sorted(repaired),
        "section_origins": {
            name: {"job_id": seed["job_id"], "output_hash": digest(previous)}
            for name in locked
        },
        "generation_settings": {
            k: profile[k]
            for k in (
                "temperature",
                "max_output_tokens",
                "context_length",
                "engine",
                "engine_version",
            )
            if k in profile
        }
        | {"thinking": True},
        "input_hash": digest(root),
        "task_hash": digest(task),
        "dependencies": lookup.dependencies,
        "tool_calls": lookup.trace,
        "attempts": attempts,
        "repair_conversation": messages,
        "review_coverage": previous.get("provenance", {}).get("review_coverage", {}),
    }
    return result, usage
