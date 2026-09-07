"""Lossless public review observations, separate from sampled model evidence."""

from datetime import datetime, timezone
import json
import re

import pyarrow as pa

from .models import digest

TEXT = pa.string()
SCHEMA = pa.schema(
    [("observed_at", pa.timestamp("us", tz="UTC"))]
    + [
        (name, TEXT)
        for name in (
            "run_id",
            "source_review_id",
            "source_instructor_id",
            "instructor_name",
            "course_label",
            "course_id",
            "course_uid",
            "review_date",
            "comment",
            "source_url",
        )
    ]
    + [("quality_rating", pa.float64()), ("difficulty_rating", pa.float64())]
)
DESCRIPTION = (
    "One review observation per run, RMP profile and review ID, deduplicated across "
    "instructor-name searches. Includes all reviews on matched profiles, without an "
    "age cutoff or LLM sampling limit. course_label and review_date retain source "
    "text; course_id/course_uid are null when the label cannot be resolved uniquely "
    "in that snapshot. source_instructor_id is the RMP profile ID, not a verified "
    "cross-source person identity. Repeated snapshots are not distinct reviews."
)


def review_rows(db, identities):
    for (run,) in db.execute("SELECT run_id FROM runs ORDER BY run_id"):
        aliases = {}
        for row in db.execute(
            "SELECT s.course_id,v.record_json FROM course_snapshots s "
            "JOIN course_versions v USING(version_id) WHERE s.run_id=?",
            (run,),
        ):
            ref = json.loads(row[1])["course_reference"]
            for subject in ref["subjects"]:
                aliases.setdefault(
                    (subject.replace(" ", ""), ref["course_number"]), set()
                ).add(row[0])
        seen = set()
        for observed_at, raw in db.execute(
            "SELECT observed_at,payload_json FROM observations "
            "WHERE run_id=? AND kind='ratings' ORDER BY observed_at DESC,entity_id",
            (run,),
        ):
            observed = datetime.fromisoformat(observed_at)
            observed = (
                observed.replace(tzinfo=timezone.utc)
                if observed.tzinfo is None
                else observed.astimezone(timezone.utc)
            )
            record = json.loads(raw)
            matched = record.get("matched_teacher_id")
            if not matched:
                continue
            for teacher in record.get("candidates", []):
                if teacher["id"] != matched:
                    continue
                instructor = f"rmp:{teacher['legacyId']}"
                for edge in teacher["ratings"]["edges"]:
                    review = edge["node"]
                    review_id = review.get("id") or "content:" + digest(review)
                    key = (instructor, review_id)
                    if key in seen:
                        continue
                    seen.add(key)
                    label = review.get("class") or ""
                    match = re.fullmatch(r"(.+?)\s*(\d{3})", label.upper().strip())
                    targets = None
                    if match:
                        for subject in match[1].strip().split("/"):
                            subject = subject.replace(" ", "")
                            if subject == "CS":
                                subject = "COMPSCI"
                            found = aliases.get((subject, int(match[2])), set())
                            targets = found if targets is None else targets & found
                    course = (
                        next(iter(targets)) if targets and len(targets) == 1 else None
                    )
                    yield {
                        "run_id": run,
                        "observed_at": observed,
                        "source_review_id": review_id,
                        "source_instructor_id": instructor,
                        "instructor_name": f"{teacher['firstName']} {teacher['lastName']}",
                        "course_label": label,
                        "course_id": course,
                        "course_uid": identities.get(course),
                        "review_date": review.get("date"),
                        "comment": review.get("comment"),
                        "source_url": f"https://www.ratemyprofessors.com/professor/{teacher['legacyId']}",
                        "quality_rating": review.get("qualityRating"),
                        "difficulty_rating": review.get("difficultyRatingRounded"),
                    }
