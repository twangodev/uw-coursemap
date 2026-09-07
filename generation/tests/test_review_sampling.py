import unittest

from uw_coursemap.course_context import sample_reviews


def review(i, instructor="current", year=2026):
    return {
        "id": str(i),
        "instructor_id": instructor,
        "date": f"{year}-01-01",
        "comment": "Feedback",
    }


class ReviewSamplingTests(unittest.TestCase):
    def test_recent_volume_does_not_displace_previous_instructor(self):
        old = review("old", "previous", 2020)
        reviews = [old] + [review(i) for i in range(100)]
        selected = sample_reviews(reviews)
        self.assertEqual(len(selected), 30)
        self.assertIn(old, selected)
        self.assertEqual(selected, sample_reviews(list(reversed(reviews))))

    def test_one_instructor_retains_reviews_across_their_timeline(self):
        reviews = [review(year, year=year) for year in range(2000, 2027)]
        selected = sample_reviews(reviews, 5)
        self.assertEqual(
            [r["date"][:4] for r in selected], ["2000", "2006", "2013", "2019", "2026"]
        )

    def test_many_instructors_include_oldest_and_newest_periods(self):
        reviews = [review(year, str(year), year) for year in range(1980, 2027)]
        selected = sample_reviews(reviews)
        self.assertEqual(len(selected), 30)
        self.assertEqual(len({r["instructor_id"] for r in selected}), 30)
        self.assertIn(reviews[0], selected)
        self.assertIn(reviews[-1], selected)

    def test_small_sets_and_empty_budget(self):
        reviews = [review(2), review(1, "previous", 2020)]
        self.assertEqual(len(sample_reviews(reviews)), 2)
        self.assertEqual(sample_reviews(reviews, 0), [])
        self.assertEqual(sample_reviews([], 30), [])
