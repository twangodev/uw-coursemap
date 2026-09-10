import json
import sqlite3
import unittest

from uwcourses.review_data import review_rows


class ReviewDataTests(unittest.TestCase):
    def test_history_deduplication_and_unresolved_labels(self):
        db = sqlite3.connect(":memory:")
        self.addCleanup(db.close)
        db.executescript("""
            CREATE TABLE runs(run_id TEXT);
            CREATE TABLE course_snapshots(run_id TEXT,course_id TEXT,version_id TEXT);
            CREATE TABLE course_versions(version_id TEXT,record_json TEXT);
            CREATE TABLE observations(run_id TEXT,kind TEXT,entity_id TEXT,observed_at TEXT,payload_json TEXT);
        """)
        record = {"course_reference": {"subjects": ["COMPSCI"], "course_number": 300}}
        db.execute("INSERT INTO course_versions VALUES('v',?)", (json.dumps(record),))
        teacher = {
            "id": "teacher",
            "legacyId": 123,
            "firstName": "Former",
            "lastName": "Teacher",
            "ratings": {
                "edges": [
                    {
                        "node": {
                            "id": key,
                            "class": label,
                            "date": "2019-01-01",
                            "comment": "Original comment",
                            "qualityRating": 4,
                            "difficultyRatingRounded": 3,
                        }
                    }
                    for key, label in [("a", "CS300"), ("b", "unknown"), ("c", "")]
                ]
            },
        }
        payload = json.dumps({"matched_teacher_id": "teacher", "candidates": [teacher]})
        for run in ["old", "new"]:
            db.execute("INSERT INTO runs VALUES(?)", (run,))
            db.execute(
                "INSERT INTO course_snapshots VALUES(?,'COMPSCI300','v')", (run,)
            )
            for name in ["alias1", "alias2"]:
                db.execute(
                    "INSERT INTO observations VALUES(?,'ratings',?,'2026-09-07',?)",
                    (run, name, payload),
                )
        rows = list(review_rows(db, {"COMPSCI300": "uid"}))
        self.assertEqual(len(rows), 6)
        self.assertEqual({row["run_id"] for row in rows}, {"old", "new"})
        self.assertEqual(sum(row["course_uid"] == "uid" for row in rows), 2)
        self.assertEqual(sum(row["course_id"] is None for row in rows), 4)
        self.assertTrue(all(row["review_date"] == "2019-01-01" for row in rows))
        self.assertTrue(all(row["comment"] == "Original comment" for row in rows))
        self.assertTrue(all(row["source_instructor_id"] == "rmp:123" for row in rows))
