"""Build anonymous daily schedule events for the landing-page campus clock."""

from collections import defaultdict
from datetime import datetime, timedelta, time
import json
from zoneinfo import ZoneInfo

ZONE = ZoneInfo("America/Chicago")


class CampusSchedule:
    def __init__(self):
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
        base = f"/data/{revision}/campus"
        manifest = {
            "timezone": "America/Chicago",
            "from": None,
            "through": None,
            "assetBase": base,
        }
        if not self.days:
            return manifest
        manifest.update({"from": min(self.days), "through": max(self.days)})
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
                json.dumps({"date": key, "events": events}, separators=(",", ":"))
            )
            date += timedelta(days=1)
        return manifest
