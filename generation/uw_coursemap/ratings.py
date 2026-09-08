"""RMP collection contracts and attributable course-review projections."""

SCHOOL_ID = "U2Nob29sLTE4NDE4"
REVIEW_FIELDS = "id class date comment qualityRating difficultyRatingRounded"
PROFILE_FIELDS = """id legacyId firstName lastName school { id legacyId name }
    avgRatingRounded avgDifficultyRounded numRatings wouldTakeAgainPercentRounded
    mandatoryAttendance { yes no neither total }
    ratingsDistribution { r1 r2 r3 r4 r5 total }"""
RATINGS = (
    "ratings(first: 100) { pageInfo { hasNextPage endCursor } edges { cursor node { "
    + REVIEW_FIELDS
    + " } } }"
)
SEARCH_QUERY = (
    """query($query: TeacherSearchQuery!, $after: String) {
    newSearch { teachers(query: $query, first: 50, after: $after) {
    pageInfo { hasNextPage endCursor } edges { node { """
    + PROFILE_FIELDS
    + " "
    + RATINGS
    + " } } } } }"
)
REVIEWS_QUERY = (
    """query($id: ID!, $after: String) { node(id: $id) {
    ... on Teacher { id ratings(first: 100, after: $after) {
    pageInfo { hasNextPage endCursor } edges { cursor node { """
    + REVIEW_FIELDS
    + " } } } } } }"
)


def instructor_names(store, run):
    names = {
        row["name"]
        for row in store.records(run, "instructors").values()
        if row.get("name")
    }
    for grades in store.records(run, "grades").values():
        for offering in grades["courseOfferings"]:
            for section in offering["sections"]:
                names.update(
                    i["name"] for i in section.get("instructors", []) if i.get("name")
                )
    return sorted(names)


def next_cursor(connection, previous=None):
    page = connection["pageInfo"]
    if not isinstance(connection["edges"], list) or not isinstance(
        page["hasNextPage"], bool
    ):
        raise ValueError("Malformed RMP pagination")
    if not page["hasNextPage"]:
        return None
    cursor = page.get("endCursor")
    if (
        not connection["edges"]
        or not isinstance(cursor, str)
        or not cursor
        or cursor == previous
    ):
        raise ValueError("RMP pagination did not advance")
    return cursor


def matched_teacher(name, candidates):
    """Keep ambiguous name matches unresolved rather than pick the first profile."""
    from uw_coursemap.name_matcher import find_best_structured_match

    scores = []
    for candidate in candidates:
        if (candidate.get("school") or {}).get("id") != SCHOOL_ID:
            continue
        match = find_best_structured_match(
            name, [candidate], threshold=80, require_exact_last=True
        )
        if match.is_match:
            scores.append((match.confidence, candidate))
    if not scores:
        return None
    best = max(score for score, _ in scores)
    winners = {
        candidate["id"]: candidate for score, candidate in scores if score == best
    }
    return next(iter(winners.values())) if len(winners) == 1 else None


def course_reviews(teacher):
    if teacher is None:
        return []
    result = []
    for edge in teacher["ratings"]["edges"]:
        review = edge["node"]
        if not all(
            isinstance(review.get(k), str) and review[k].strip()
            for k in ("id", "class", "date", "comment")
        ):
            continue  # Raw records are retained even without usable course attribution.
        result.append(
            {
                "course_id": review["class"],
                "comment": review["comment"],
                "date": review["date"],
                "source_url": f"https://www.ratemyprofessors.com/professor/{teacher['legacyId']}",
                "instructor_id": f"rmp:{teacher['legacyId']}",
                "instructor_name": f"{teacher['firstName']} {teacher['lastName']}",
                "source_review_id": review["id"],
                "quality_rating": review.get("qualityRating"),
                "difficulty_rating": review.get("difficultyRatingRounded"),
            }
        )
    return result
