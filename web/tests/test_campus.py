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
                (Path(root) / "data/release/campus/2026-09-09.json").read_text()
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
