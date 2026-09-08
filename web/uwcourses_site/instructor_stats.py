"""Display statistics from captured reviews, with conservative profile matching."""

from collections import defaultdict


def name_key(name):
    return "".join(char for char in (name or "").casefold() if char.isalnum())


def review_stats(reviews):
    quality = [
        r["quality_rating"]
        for r in reviews
        if r.get("quality_rating") is not None and 1 <= r["quality_rating"] <= 5
    ]
    difficulty = [
        r["difficulty_rating"]
        for r in reviews
        if r.get("difficulty_rating") is not None and 1 <= r["difficulty_rating"] <= 5
    ]
    return {
        "review_count": len(reviews),
        "quality": round(sum(quality) / len(quality), 2) if quality else None,
        "difficulty": round(sum(difficulty) / len(difficulty), 2)
        if difficulty
        else None,
        "quality_count": len(quality),
        "difficulty_count": len(difficulty),
    }


def attach_ratings(instructors, reviews):
    latest = {}
    for review in reviews:
        key = (review["source_instructor_id"], review["source_review_id"])
        if key not in latest or str(review["observed_at"]) > str(
            latest[key]["observed_at"]
        ):
            latest[key] = review
    profiles = defaultdict(list)
    names = defaultdict(set)
    identities = defaultdict(set)
    for instructor in instructors.values():
        if instructor.get("source") == "enrollment" and instructor.get(
            "source_instructor_id"
        ):
            identities[name_key(instructor["name"])].add(
                instructor["source_instructor_id"]
            )
    for review in latest.values():
        profiles[review["source_instructor_id"]].append(review)
        names[name_key(review["instructor_name"])].add(review["source_instructor_id"])
    for instructor in instructors.values():
        name = name_key(instructor["name"])
        ids = names[name]
        if len(ids) != 1 or len(identities[name]) > 1:
            continue
        profile_id = next(iter(ids))
        captured = profiles[profile_id]
        by_course = defaultdict(list)
        for review in captured:
            if review.get("course_uid"):
                by_course[review["course_uid"]].append(review)
        instructor["ratings"] = {
            **review_stats(captured),
            "profile_id": profile_id,
            "source_url": captured[0]["source_url"],
            "match_basis": "exact_name",
            "observed_at": str(max(r["observed_at"] for r in captured)),
            "courses": {uid: review_stats(rs) for uid, rs in by_course.items()},
        }
