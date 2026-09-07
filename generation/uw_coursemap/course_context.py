"""Read-only, bounded course evidence from one immutable snapshot."""

import json
import re

from .models import digest


def text_view(text):
    # Some historical parser records contain escaped display characters.
    for escaped, char in [
        (r"\xa0", " "),
        (r"\u00a0", " "),
        (r"\u200b", ""),
        ("\u200b", ""),
    ]:
        text = (text or "").replace(escaped, char)
    return " ".join((text or "").split())


class CourseContext:
    def __init__(self, store, run):
        self.courses = store.records(run, "courses")
        self.sources = dict(
            store.db.execute(
                "SELECT entity_id,source_url FROM observations WHERE run_id=? AND kind='courses' ORDER BY entity_id,source",
                (run,),
            )
        )
        self.aliases = {}
        for key, course in self.courses.items():
            ref = course["course_reference"]
            for subject in ref["subjects"]:
                self.aliases.setdefault((subject, ref["course_number"]), set()).add(key)
        self.history = {}
        self.reviews = {}
        terms = store.records(run, "terms")
        for row in store.db.execute(
            "SELECT payload_json FROM observations WHERE run_id=? AND kind='grades' ORDER BY entity_id",
            (run,),
        ):
            grade = json.loads(row[0])
            ref = grade["course_reference"]
            targets = set().union(
                *(
                    self.aliases.get((s, ref["course_number"]), set())
                    for s in ref["subjects"]
                )
            )
            if len(targets) != 1:
                continue  # Preserve the scraper's refusal to guess ambiguous cross-listings.
            key = targets.pop()
            for offering in grade.get("courseOfferings", []):
                term = str(offering["termCode"])
                self.history.setdefault(key, []).append(
                    {
                        "term": term,
                        "term_name": terms.get(term, {}).get("name"),
                        "instructors": sorted(
                            {
                                i["name"]
                                for section in offering.get("sections", [])
                                for i in section.get("instructors", [])
                                if i.get("name")
                            }
                        ),
                        "grade_counts": offering.get("cumulative", {}),
                    }
                )
        # Old RMP records lack course/date attribution. Never attach a professor's
        # general comments to all of their classes. Only explicitly attributed rows
        # are eligible if a source adapter later supplies this normalized shape.
        for record in store.records(run, "ratings").values():
            for review in record.get("course_reviews", []):
                required = (
                    "course_id",
                    "comment",
                    "date",
                    "source_url",
                    "instructor_id",
                )
                if not all(
                    isinstance(review.get(k), str) and review[k] for k in required
                ):
                    continue
                key = self.resolve(review["course_id"])
                if key:
                    item = {k: review[k] for k in required}
                    item["course_id"] = key
                    item["id"] = digest(item)[:24]
                    self.reviews.setdefault(key, []).append(item)

    def resolve(self, identifier):
        if identifier in self.courses:
            return identifier
        match = re.fullmatch(r"(.+?)\s*(\d{3})", identifier.upper().strip())
        if not match:
            return None
        subjects = [s.replace(" ", "") for s in match[1].strip().split("/")]
        subjects = ["COMPSCI" if s in {"CS", "COMPSCI"} else s for s in subjects]
        targets = None
        for s in subjects:
            found = self.aliases.get((s, int(match[2])), set())
            targets = found if targets is None else targets & found
        return next(iter(targets)) if targets and len(targets) == 1 else None

    def get(self, identifier):
        key = self.resolve(identifier)
        if key is None:
            return None
        course = self.courses[key]
        req = course.get("prerequisites") or {}
        history = sorted(
            self.history.get(key, []), key=lambda x: (x["term"], digest(x))
        )
        return {
            "course_id": key,
            "source_url": self.sources.get(key),
            "course_reference": course["course_reference"],
            "title": course["course_title"],
            "description": text_view(course.get("description", "")),
            "requirements_text": text_view(req.get("prerequisites_text", "")),
            "linked_courses": req.get("course_references", []),
            "history": {"observations": len(history), "recent_offerings": history[-8:]},
            "reviews": sorted(
                self.reviews.get(key, []), key=lambda x: (x["date"], x["id"])
            )[-30:],
            "original_requirements": {
                "text": req.get("prerequisites_text", ""),
                "ast": req.get("abstract_syntax_tree"),
            },
        }

    def fingerprint(self, identifier):
        return digest(self.get(identifier))


class CourseLookup:
    def __init__(self, context, root, max_calls=6, max_depth=2, max_chars=12000):
        self.context = context
        self.root = root
        self.depths = {root: 0}
        self.dependencies = {}
        self.trace = []
        self.calls = 0
        self.chars = 0
        self.max_calls, self.max_depth, self.max_chars = max_calls, max_depth, max_chars
        self.evidence = {root: context.get(root)}

    def get_course(self, identifier, from_course):
        result = self._get_course(identifier, from_course)
        self.trace.append(
            {
                "tool": "get_course",
                "course_id": identifier,
                "from_course": from_course,
                "result": result,
            }
        )
        return result

    def _get_course(self, identifier, from_course):
        self.calls += 1
        if self.calls > self.max_calls:
            return {"error": "Course lookup budget exhausted"}
        parent = self.context.resolve(from_course)
        key = self.context.resolve(identifier)
        if parent not in self.depths:
            return {"error": "from_course must be a course already provided"}
        if self.depths[parent] >= self.max_depth:
            return {"error": "Maximum lookup depth reached"}
        # Missing results are dependencies too: a newly available course invalidates cache.
        self.dependencies[identifier] = self.context.fingerprint(identifier)
        if key is None:
            result = {
                "error": "Course not found in this snapshot",
                "course_id": identifier,
            }
        elif key in self.depths:
            result = {"course_id": key, "already_provided": True}
        else:
            full = self.context.get(key)
            result = {
                k: full[k]
                for k in [
                    "course_id",
                    "course_reference",
                    "title",
                    "description",
                    "requirements_text",
                    "linked_courses",
                ]
            }
            if len(json.dumps(result)) + self.chars > self.max_chars:
                result = {"error": "Course evidence budget exhausted"}
            else:
                self.chars += len(json.dumps(result))
                self.depths[key] = self.depths[parent] + 1
                self.evidence[key] = result
        return result
