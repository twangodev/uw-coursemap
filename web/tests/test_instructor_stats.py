import unittest
from uwcourses_site.instructor_stats import attach_ratings


class InstructorStatsTests(unittest.TestCase):
    def review(self, id="one", observed="2026-09-01", quality=4):
        return dict(
            source_instructor_id="rmp:1",
            source_review_id=id,
            observed_at=observed,
            instructor_name="Hobbes Legault",
            course_uid="cs300",
            source_url="https://www.ratemyprofessors.com/professor/1",
            quality_rating=quality,
            difficulty_rating=3,
        )

    def test_uses_latest_review_once_and_retains_course_scope(self):
        instructors = {
            "i": dict(
                name="Hobbes Legault",
                source="enrollment",
                source_instructor_id="legault",
            )
        }
        attach_ratings(
            instructors,
            [
                self.review(),
                self.review(observed="2026-09-02", quality=2),
                self.review(id="two", quality=4),
            ],
        )
        stats = instructors["i"]["ratings"]
        self.assertEqual(stats["review_count"], 2)
        self.assertEqual(stats["quality"], 3)
        self.assertEqual(stats["courses"]["cs300"]["quality"], 3)

    def test_ambiguous_profiles_are_not_attached(self):
        instructors = {"i": dict(name="Hobbes Legault")}
        other = {**self.review(), "source_instructor_id": "rmp:2"}
        attach_ratings(instructors, [self.review(), other])
        self.assertNotIn("ratings", instructors["i"])

    def test_distinct_enrollment_identities_are_not_collapsed_by_name(self):
        instructors = {
            key: dict(
                name="Hobbes Legault", source="enrollment", source_instructor_id=key
            )
            for key in ["one", "two"]
        }
        attach_ratings(instructors, [self.review()])
        self.assertTrue(all("ratings" not in row for row in instructors.values()))


if __name__ == "__main__":
    unittest.main()
