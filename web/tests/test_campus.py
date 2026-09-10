from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest
from uwcourses_site.campus import CampusSchedule
from datetime import datetime


def stamp(value):
    return int(datetime.fromisoformat(value).timestamp() * 1000)


class CampusTests(unittest.TestCase):
    def row(self, **kwargs):
        return {
            "meeting_type": "CLASS",
            "meeting_id": "a",
            "starts_at": "2026-09-09T14:00:00+00:00",
            "ends_at": "2026-09-09T15:00:00+00:00",
            "building": "Science",
            "room": "100",
            **kwargs,
        }

    def test_crosslists_invalid_and_exam(self):
        schedule = CampusSchedule()
        schedule.add(self.row())
        schedule.add(self.row(meeting_id="crosslist", building=" SCIENCE "))
        schedule.add(self.row(meeting_type="EXAM"))
        schedule.add(self.row(ends_at="bad"))
        with TemporaryDirectory() as root:
            manifest = schedule.write(Path(root), "release")
            day = json.loads(
                (Path(root) / "data/release/campus/v2/2026-09-09.json").read_text()
            )
            self.assertEqual(
                day["events"],
                [
                    [stamp("2026-09-09T14:00:00+00:00"), 1, 0],
                    [stamp("2026-09-09T15:00:00+00:00"), 0, 1],
                ],
            )
            self.assertEqual(manifest["from"], "2026-09-09")

    def test_midnight_and_winter_timezone(self):
        schedule = CampusSchedule()
        schedule.add(
            self.row(
                starts_at="2026-12-10T05:30:00+00:00",
                ends_at="2026-12-10T06:30:00+00:00",
            )
        )
        self.assertEqual(
            dict(schedule.days["2026-12-09"]),
            {
                stamp("2026-12-10T05:30:00+00:00"): [1, 0],
                stamp("2026-12-10T06:00:00+00:00"): [0, 1],
            },
        )
        self.assertEqual(
            dict(schedule.days["2026-12-10"]),
            {
                stamp("2026-12-10T06:00:00+00:00"): [1, 0],
                stamp("2026-12-10T06:30:00+00:00"): [0, 1],
            },
        )

    def test_fall_back_keeps_repeated_hour_order(self):
        schedule = CampusSchedule()
        schedule.add(
            self.row(
                starts_at="2026-11-01T06:45:00+00:00",
                ends_at="2026-11-01T07:15:00+00:00",
            )
        )
        events = sorted(schedule.days["2026-11-01"].items())
        self.assertEqual([value for _, value in events], [[1, 0], [0, 1]])

    def test_empty(self):
        with TemporaryDirectory() as root:
            self.assertIsNone(CampusSchedule().write(Path(root), "release")["from"])

    def test_enrollment_deduplicates_crosslists_and_ignores_ambiguous_matches(self):
        section = {
            "section_uid": "one",
            "section_type": "LEC",
            "section_number": "001",
            "start_date": "2026-09-01T05:00:00Z",
            "end_date": "2026-12-10T06:00:00Z",
            "enrolled": 100,
        }
        schedule = CampusSchedule(
            {
                "a": [section],
                "b": [section],
                "ambiguous": [section, {**section, "section_uid": "two"}],
            }
        )
        schedule.add(self.row(course_uid="a", name="LEC 001 #1"))
        schedule.add(self.row(course_uid="b", name="LEC 001 #1", meeting_id="copy"))
        schedule.add(self.row(course_uid="ambiguous", name="LEC 001 #1", room="200"))
        with TemporaryDirectory() as root:
            schedule.write(Path(root), "release")
            day = json.loads(
                (Path(root) / "data/release/campus/v2/2026-09-09.json").read_text()
            )
        self.assertEqual(day["events"][0][1], 2)
        self.assertEqual(
            day["enrollmentEvents"],
            [
                [stamp("2026-09-09T14:00:00+00:00"), 100, 0, 1, 0],
                [stamp("2026-09-09T15:00:00+00:00"), 0, 100, 0, 1],
            ],
        )

    def test_missing_enrollment_is_not_zero_and_term_dates_disambiguate(self):
        base = {
            "section_type": "LEC",
            "section_number": "001",
            "enrolled": 40,
            "start_date": "2026-09-01T05:00:00Z",
            "end_date": "2026-12-10T06:00:00Z",
        }
        schedule = CampusSchedule(
            {
                "a": [
                    {**base, "section_uid": "current"},
                    {**base, "section_uid": "past", "end_date": "2026-08-01T05:00:00Z"},
                ],
                "b": [{**base, "section_uid": "missing", "enrolled": None}],
            }
        )
        schedule.add(self.row(course_uid="a", name="LEC 001 #1"))
        schedule.add(self.row(course_uid="b", name="LEC 001 #1", room="200"))
        with TemporaryDirectory() as root:
            schedule.write(Path(root), "release")
            day = json.loads(
                (Path(root) / "data/release/campus/v2/2026-09-09.json").read_text()
            )
        self.assertEqual(day["enrollmentEvents"][0][1:], [40, 0, 1, 0])
