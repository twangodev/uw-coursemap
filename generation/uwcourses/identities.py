"""Persistent catalog identities; ambiguous aliases never merge existing entities."""

import json
from pathlib import Path

from .models import digest


class CourseIdentities:
    def __init__(self, path=None):
        self.path = Path(path) if path else None
        self.assignments = {}
        self.aliases = {}
        if self.path and self.path.exists():
            value = json.loads(self.path.read_text())
            if value["version"] != 1:
                raise ValueError("Unsupported course identity registry")
            self.assignments = value["assignments"]
            for label, identity in self.assignments.items():
                for alias in self.references(label):
                    self.aliases.setdefault(alias, set()).add(identity)

    @staticmethod
    def references(label):
        subjects, number = label.rsplit(" ", 1)
        return [f"{subject} {int(number)}" for subject in subjects.split("/")]

    def identify(self, label):
        if label in self.assignments:
            return self.assignments[label]
        aliases = self.references(label)
        known = set().union(*(self.aliases.get(alias, set()) for alias in aliases))
        identity = (
            next(iter(known)) if len(known) == 1 else "course_" + digest(label)[:24]
        )
        self.assignments[label] = identity
        for alias in aliases:
            self.aliases.setdefault(alias, set()).add(identity)
        return identity

    def save(self):
        value = {"version": 1, "assignments": dict(sorted(self.assignments.items()))}
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")
            temporary.replace(self.path)
        return value


def catalog_identities(db, registry_path=None):
    registry = CourseIdentities(registry_path)
    identities = {}
    for row in db.execute("""SELECT s.course_id, min(r.observed_at) AS first_seen
        FROM course_snapshots s JOIN runs r USING(run_id)
        GROUP BY s.course_id ORDER BY first_seen,s.course_id"""):
        identities[row["course_id"]] = registry.identify(row["course_id"])
    registry.save()
    return identities
