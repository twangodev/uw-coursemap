import json
import sqlite3
import unittest
from uwcourses_site.discovery import build_discovery


class DiscoveryTests(unittest.TestCase):
    def test_latest_reviews_keep_unmapped_courses_and_profiles_separate(self):
        db = sqlite3.connect(":memory:")
        db.executescript(
            "CREATE TABLE courses(uid,payload);CREATE TABLE grades(uid,term,section,payload);"
        )
        db.execute(
            "INSERT INTO courses VALUES(?,?)",
            (
                "c",
                json.dumps({"offerings": [{"term_id": "1272"}, {"term_id": "1272"}]}),
            ),
        )
        db.executemany(
            "INSERT INTO grades VALUES(?,?,?,?)",
            [("c", "1264", "", '{"a":10}'), ("c", "1264", "001", '{"a":10}')],
        )
        base = {
            "source_instructor_id": "p",
            "source_review_id": "r",
            "course_uid": None,
            "review_date": None,
            "observed_at": "2026-01-01",
            "comment": "old",
        }
        build_discovery(
            db,
            [
                base,
                {**base, "observed_at": "2026-02-01", "comment": "new"},
                {**base, "source_instructor_id": "q"},
            ],
        )
        self.assertEqual(db.execute("SELECT COUNT(*) FROM reviews").fetchone()[0], 2)
        self.assertEqual(
            json.loads(
                db.execute(
                    "SELECT payload FROM reviews WHERE profile_id='p'"
                ).fetchone()[0]
            )["comment"],
            "new",
        )
        self.assertEqual(
            db.execute("SELECT SUM(a) FROM grade_summaries").fetchone()[0], 10
        )
        self.assertEqual(db.execute("SELECT COUNT(*) FROM offerings").fetchone()[0], 1)
