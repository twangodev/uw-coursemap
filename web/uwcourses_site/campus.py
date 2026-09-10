"""Build anonymous daily schedule events for the landing-page campus clock."""

from collections import defaultdict
from datetime import datetime, timedelta, time
import json
import math
import re
from zoneinfo import ZoneInfo

ZONE = ZoneInfo("America/Chicago")


class CampusSchedule:
    def __init__(self, sections=None):
        self.sections = sections or {}
        self.sessions = {}
        self.seen = set()
        self.days = defaultdict(lambda: defaultdict(lambda: [0, 0]))

    def add(self, row):
        if row.get("meeting_type") != "CLASS":
            return
        try:
            start = datetime.fromisoformat(str(row["starts_at"]).replace("Z", "+00:00"))
            end = datetime.fromisoformat(str(row["ends_at"]).replace("Z", "+00:00"))
            if (
                start.tzinfo is None
                or end.tzinfo is None
                or end.timestamp() <= start.timestamp()
            ):
                return
            start, end = start.astimezone(ZONE), end.astimezone(ZONE)
        except (KeyError, TypeError, ValueError):
            return
        building = str(row.get("building") or "").strip().casefold()
        room = str(row.get("room") or "").strip().casefold()
        location = (building, room) if building and room else (row.get("meeting_id"),)
        if location == (None,):
            return
        key = (start.isoformat(), end.isoformat(), location)
        session = self.sessions.setdefault(
            key, {"start": start, "end": end, "sections": {}, "unknown": False}
        )
        session.setdefault("courses", {})[
            (str(row.get("course_id") or ""), str(row.get("name") or "").split(" #")[0])
        ] = True
        session.setdefault("instructors", set()).update(
            row.get("instructor_names") or []
        )
        session["room"] = str(row.get("room") or "")
        latitude, longitude = row.get("latitude"), row.get("longitude")
        if (
            building
            and isinstance(latitude, (int, float))
            and isinstance(longitude, (int, float))
            and math.isfinite(latitude)
            and math.isfinite(longitude)
            and -90 <= latitude <= 90
            and -180 <= longitude <= 180
        ):
            session["building"] = (
                building,
                str(row["building"]).strip(),
                latitude,
                longitude,
            )
        match = re.fullmatch(r"([A-Z]+)\s+(\S+)\s+#\d+", str(row.get("name", "")))
        candidates = []
        if match:
            for section in self.sections.get(row.get("course_uid"), []):
                if (
                    section.get("section_type"),
                    section.get("section_number"),
                ) != match.groups():
                    continue
                try:
                    first = datetime.fromisoformat(
                        str(section["start_date"]).replace("Z", "+00:00")
                    )
                    last = datetime.fromisoformat(
                        str(section["end_date"]).replace("Z", "+00:00")
                    )
                    if (
                        first.astimezone(ZONE).date()
                        <= start.date()
                        <= last.astimezone(ZONE).date()
                    ):
                        candidates.append(section)
                except (KeyError, ValueError, TypeError):
                    continue
        candidates = {s["section_uid"]: s for s in candidates}
        if len(candidates) == 1:
            uid, section = next(iter(candidates.items()))
            enrolled = section.get("enrolled")
            if isinstance(enrolled, int) and enrolled >= 0:
                session["sections"][uid] = enrolled
            else:
                session["unknown"] = True
        else:
            session["unknown"] = True
        if key in self.seen:
            return
        self.seen.add(key)
        while start.timestamp() < end.timestamp():
            midnight = datetime.combine(start.date() + timedelta(days=1), time(), ZONE)
            stop = min(end, midnight, key=lambda value: value.timestamp())
            events = self.days[start.date().isoformat()]
            events[int(start.timestamp() * 1000)][0] += 1
            events[int(stop.timestamp() * 1000)][1] += 1
            start = stop

    def write(self, static, revision):
        base = f"/data/{revision}/campus/v4"
        manifest = {
            "timezone": "America/Chicago",
            "from": None,
            "through": None,
            "assetBase": base,
        }
        if not self.days:
            return manifest
        manifest.update({"from": min(self.days), "through": max(self.days)})
        enrollment = defaultdict(lambda: defaultdict(lambda: [0, 0, 0, 0]))
        buildings = defaultdict(dict)
        for session in self.sessions.values():
            known = not session["unknown"] and bool(session["sections"])
            start, end = session["start"], session["end"]
            seats = sum(session["sections"].values())
            while start.timestamp() < end.timestamp():
                midnight = datetime.combine(
                    start.date() + timedelta(days=1), time(), ZONE
                )
                stop = min(end, midnight, key=lambda value: value.timestamp())
                day = start.date().isoformat()
                first, last = (
                    int(start.timestamp() * 1000),
                    int(stop.timestamp() * 1000),
                )
                if known:
                    events = enrollment[day]
                    events[first][0] += seats
                    events[first][2] += 1
                    events[last][1] += seats
                    events[last][3] += 1
                if "building" in session:
                    key, name, latitude, longitude = session["building"]
                    place = buildings[day].setdefault(
                        key,
                        {
                            "name": name,
                            "latitude": latitude,
                            "longitude": longitude,
                            "events": defaultdict(lambda: [0, 0]),
                            "sessions": [],
                        },
                    )
                    place["events"][first][0] += 1
                    place["events"][last][1] += 1
                    place["sessions"].append(
                        {
                            "startsAt": int(session["start"].timestamp() * 1000),
                            "endsAt": int(session["end"].timestamp() * 1000),
                            "room": session["room"],
                            "enrolled": seats if known else None,
                            "courses": [
                                {"code": code, "section": section}
                                for code, section in sorted(session["courses"])
                                if code
                            ],
                            "instructors": sorted(session["instructors"]),
                        }
                    )
                start = stop
        date = datetime.fromisoformat(manifest["from"]).date()
        last = datetime.fromisoformat(manifest["through"]).date()
        directory = static / base.lstrip("/")
        directory.mkdir(parents=True, exist_ok=True)
        while date <= last:
            key = date.isoformat()
            events = [
                [minute, *counts]
                for minute, counts in sorted(self.days.get(key, {}).items())
            ]
            (directory / f"{key}.json").write_text(
                json.dumps(
                    {
                        "date": key,
                        "events": events,
                        "buildings": [
                            {
                                **place,
                                "events": [
                                    [at, *counts]
                                    for at, counts in sorted(place["events"].items())
                                ],
                            }
                            for _, place in sorted(buildings.get(key, {}).items())
                        ],
                        "enrollmentEvents": [
                            [at, *counts]
                            for at, counts in sorted(enrollment.get(key, {}).items())
                        ],
                    },
                    separators=(",", ":"),
                )
            )
            date += timedelta(days=1)
        return manifest
