"""Pure source reconciliation followed by independently checkpointed enrichment."""

import asyncio
import json
import os
import random

from .models import canonical, digest


def plain(value):
    if hasattr(value, "to_dict"):
        return plain(value.to_dict())
    if isinstance(value, dict):
        result = {str(key): plain(v) for key, v in value.items()}
        for key in (
            "subjects",
            "course_references",
            "satisfies",
            "instructors",
            "courses_taught",
        ):
            if isinstance(result.get(key), list):
                result[key] = sorted(result[key], key=canonical)
        return result
    if isinstance(value, set):
        return sorted((plain(v) for v in value), key=canonical)
    if isinstance(value, (tuple, list)):
        return [plain(v) for v in value]
    return value


def reconcile(store, run):
    from course import Course
    from enrollment import apply_enrollment
    from enrollment_data import EnrollmentData, MadgradesData, TermData
    from instructors import FullInstructor, RMPData, merge_instructors
    from name_matcher import find_best_name_match, find_best_structured_match
    from sanitization import sanitize_instructor_id

    EnrollmentData.MeetingLocation._all_locations.clear()
    courses = {
        Course.Reference.from_json(data["course_reference"]): Course.from_json(data)
        for data in store.records(run, "courses").values()
    }
    aliases = {}
    for ref in courses:
        for subject in ref.subjects:
            key = (subject, ref.course_number)
            if key in aliases and aliases[key] != ref:
                raise ValueError(f"Ambiguous course alias: {key}")
            aliases[key] = ref

    def candidates_for(data):
        return {
            aliases[(s, data["course_number"])]
            for s in data["subjects"]
            if (s, data["course_number"]) in aliases
        }

    def resolve(data):
        candidates = candidates_for(data)
        if len(candidates) > 1:
            raise ValueError(f"Ambiguous source course: {data}")
        return next(iter(candidates), None)

    terms = {code: data["name"] for code, data in store.records(run, "terms").items()}
    unmatched = {"grades": [], "offerings": [], "ambiguous_grades": {}}
    for key, data in store.records(run, "grades").items():
        candidates = candidates_for(data["course_reference"])
        if len(candidates) > 1:
            # Historical cross-listings can map to several distinct current
            # courses. Preserve raw grades without choosing an arbitrary owner.
            unmatched["grades"].append(key)
            unmatched["ambiguous_grades"][key] = sorted(str(ref) for ref in candidates)
            continue
        ref = next(iter(candidates), None)
        if ref is None:
            unmatched["grades"].append(key)
            continue
        grades = MadgradesData.from_response(data)
        courses[ref].cumulative_grade_data = grades.cumulative
        for term, grade in grades.by_term.items():
            if term not in terms:
                raise ValueError(f"Grade references unknown term: {term}")
            courses[ref].term_data[term] = TermData(None, grade)

    emails, meetings = {}, {}
    for key, data in store.records(run, "offerings").items():
        ref = resolve(data["course_reference"])
        if ref is None:
            unmatched["offerings"].append(key)
            continue
        original_ref = Course.Reference.from_json(data["course_reference"])
        # Preserve the existing parser, including its DST and room-capacity logic.
        result = apply_enrollment(
            data["hit"],
            data["sections"],
            data["term"],
            {int(k): v for k, v in terms.items()},
            {original_ref: courses[ref]},
        )
        if result is None:
            unmatched["offerings"].append(key)
            continue
        names, occurrences, _ = result
        emails.update(names)
        for meeting in occurrences:
            meeting.course_reference = ref
        meetings.setdefault(ref, set()).update(occurrences)
        courses[ref].has_meetings = bool(meetings[ref])

    additional = {
        name
        for course in courses.values()
        for term in course.term_data.values()
        if term.grade_data
        for name in (term.grade_data.instructors or [])
        if name
    }
    asyncio.run(
        merge_instructors(
            additional, emails, courses, str(store.root / "runs" / run / "name-cache")
        )
    )
    faculty = store.records(run, "faculty")
    ratings = store.records(run, "ratings")
    instructors = {}
    for name, email in sorted(emails.items()):
        official = find_best_name_match(
            query_name=name,
            candidates=list(faculty),
            threshold=80,
            require_exact_last=True,
        )
        details = faculty.get(official.matched_item, {}) if official.is_match else {}
        rating_record = ratings.get(name, {})
        candidates = rating_record.get("candidates", [])
        if "matched_teacher_id" in rating_record:
            candidates = [
                c for c in candidates if c["id"] == rating_record["matched_teacher_id"]
            ]
        match = find_best_structured_match(
            query_name=name,
            candidates=candidates,
            first_name_key="firstName",
            last_name_key="lastName",
            threshold=80,
            require_exact_last=True,
        )
        rating = RMPData.from_rmp_data(match.matched_item) if match.is_match else None
        identifier = sanitize_instructor_id(name)
        if not identifier:
            raise ValueError(f"Invalid instructor identifier: {name}")
        inst = FullInstructor(
            name,
            email,
            rating,
            details.get("position"),
            details.get("department"),
            details.get("credentials"),
            details.get("name")
            or (official.matched_item if official.is_match else None),
        )
        if identifier not in instructors or (
            rating and not instructors[identifier].rmp_data
        ):
            instructors[identifier] = inst
    return courses, instructors, meetings, terms, unmatched


def encode_state(courses, instructors, meetings, terms, unmatched):
    return plain(
        {
            "courses": courses,
            "instructors": instructors,
            "meetings": meetings,
            "terms": terms,
            "unmatched": unmatched,
        }
    )


def decode_state(state):
    from course import Course
    from enrollment_data import EnrollmentData
    from instructors import FullInstructor

    courses = {
        Course.Reference.from_string(key): Course.from_json(value)
        for key, value in state["courses"].items()
    }
    instructors = {
        key: FullInstructor.from_json(value)
        for key, value in state["instructors"].items()
    }
    meetings = {
        Course.Reference.from_string(key): {
            EnrollmentData.Meeting.from_json(m) for m in value
        }
        for key, value in state["meetings"].items()
    }
    return courses, instructors, meetings, state["terms"], state["unmatched"]


def derive(store, run):
    config = json.loads(store.run(run)["config_json"])
    inputs = store.input_hash(run)
    for key in ("embedding_revision", "keyword_revision"):
        if not config.get(key):
            raise ValueError(f"Run must record {key}")
    os.environ["COURSEMAP_EMBEDDING_REVISION"] = config["embedding_revision"]
    os.environ["COURSEMAP_KEYWORD_REVISION"] = config["keyword_revision"]
    # Model identity includes immutable revisions, while input-text hashes allow reuse.
    if config.get("model_profiles"):
        os.environ["COURSEMAP_MODEL_PROFILES"] = canonical(config["model_profiles"])
    else:
        os.environ.pop("COURSEMAP_MODEL_PROFILES", None)
    cache = str(getattr(store, "cache_root", store.root / "models"))
    stages = ("reconcile", "aggregate", "optimize", "graph")
    state = None
    for stage in stages:
        stamp = digest({"inputs": inputs, "stage": stage, "config": config})
        row = store.db.execute(
            "SELECT input_hash,payload_json FROM artifacts WHERE run_id=? AND name=?",
            (run, stage),
        ).fetchone()
        if row and row[0] == stamp:
            payload = json.loads(row[1])
        elif stage == "reconcile":
            payload = encode_state(*reconcile(store, run))
        else:
            courses, instructors, meetings, terms, unmatched = decode_state(state)
            if stage == "aggregate":
                from aggregate import aggregate_courses, aggregate_instructors

                instructor_stats = aggregate_instructors(courses, instructors)
                stats, explorer = aggregate_courses(
                    courses, instructors.values(), cache
                )
                payload = encode_state(courses, instructors, meetings, terms, unmatched)
                payload["statistics"] = plain({**instructor_stats, **stats})
                payload["explorer"] = plain(explorer)
            elif stage == "optimize":
                from embeddings import get_model, optimize_prerequisites

                asyncio.run(
                    optimize_prerequisites(
                        cache,
                        get_model(cache),
                        courses,
                        config["max_prerequisites"],
                        max_retries=3,
                        strict=True,
                    )
                )
                payload = {
                    **state,
                    **encode_state(courses, instructors, meetings, terms, unmatched),
                }
            else:
                from cytoscape import (
                    build_graphs,
                    cleanup_graphs,
                    generate_styles,
                    generate_style_from_graph,
                )
                from webscrape import build_subject_to_courses

                global_graph, subjects, per_course = build_graphs(
                    courses, build_subject_to_courses(courses)
                )
                cleanup_graphs(global_graph, subjects, per_course)
                from color import generate_accessible_color

                parents = {
                    node["data"]["id"]
                    for node in global_graph
                    if node["data"].get("type") == "compound"
                }
                colors = {
                    parent: generate_accessible_color(random.Random(digest(parent)))
                    for parent in sorted(parents)
                }
                subject_styles = generate_styles(subjects, colors)
                payload = {
                    **state,
                    "graphs": plain(
                        {
                            "global": global_graph,
                            "subjects": subjects,
                            "courses": per_course,
                            "global_style": generate_style_from_graph(
                                global_graph, colors
                            ),
                            "subject_styles": subject_styles,
                        }
                    ),
                }
        store.artifact(run, stage, payload, stamp, config)
        state = payload
    return state


def write_compatibility(store, run, directory):
    from save import write_data

    state = store.get_artifact(run, "graph")
    courses, instructors, meetings, terms, _ = decode_state(state)
    graphs = state["graphs"]
    config = json.loads(store.run(run)["config_json"])
    write_data(
        str(directory),
        config["sitemap_base"],
        {k: v["name"] for k, v in store.records(run, "subjects").items()},
        {c.get_identifier(): plain(c) for c in courses.values()},
        graphs["global"],
        graphs["subjects"],
        graphs["courses"],
        graphs["global_style"],
        graphs["subject_styles"],
        plain(instructors),
        terms,
        state["statistics"],
        state["explorer"],
        {
            key: sorted(values, key=lambda m: canonical(plain(m)))
            for key, values in meetings.items()
        },
        updated_on=store.run(run)["observed_at"],
    )
