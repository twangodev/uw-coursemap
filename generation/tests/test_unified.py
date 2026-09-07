import json
from pathlib import Path
import unittest

from uw_coursemap.course_context import CourseLookup, text_view
from uw_coursemap.models import digest
from uw_coursemap.unified import generate_unified, validate_section

TASK = Path(__file__).resolve().parents[2] / "inference/tasks/course_enrichment.json"


def course(key, description="Programming using objects.", requirements="None"):
    return {
        "course_id": key,
        "course_reference": {
            "subjects": ["COMPSCI"],
            "course_number": int(key.split()[-1]),
        },
        "title": "Programming",
        "description": description,
        "requirements_text": requirements,
        "linked_courses": [],
        "history": {"observations": 0, "recent_offerings": []},
        "reviews": [],
        "original_requirements": {"text": requirements, "ast": None},
    }


class Context:
    def __init__(self):
        self.courses = {
            key: course(key)
            for key in ["COMPSCI 300", "COMPSCI 200", "COMPSCI 100", "COMPSCI 400"]
        }

    def resolve(self, key):
        return key if key in self.courses else None

    def get(self, key):
        return self.courses.get(key)

    def fingerprint(self, key):
        return digest(self.get(key))


class UnifiedTests(unittest.TestCase):
    def setUp(self):
        self.task = json.loads(TASK.read_text())
        self.context = Context()
        self.root = self.context.get("COMPSCI 300")
        self.lookup = CourseLookup(self.context, "COMPSCI 300")
        self.profile = {"model": "test", "revision": "a" * 40}
        self.search = {
            "summary": {
                "text": "Object-oriented programming.",
                "evidence": [
                    {
                        "course_id": "COMPSCI 300",
                        "field": "description",
                        "quote": "Programming using objects.",
                    }
                ],
            },
            "topics": [],
            "skills_taught": [],
            "assumed_background": [],
            "search_phrases": ["object oriented programming"],
        }
        self.requirements = {"status": "none", "root": None, "nodes": [], "notes": []}
        self.experience = {"status": "insufficient_evidence", "themes": []}

    def test_independent_sections_keep_search_when_ast_fails(self):
        bad = {**self.requirements, "root": "missing"}
        calls = []

        def transport(*args):
            calls.append(args)
            return {
                "search_profile": self.search if len(calls) == 1 else None,
                "requirements": bad,
                "student_experience": self.experience,
                "lookups": [],
            }, {"completion_tokens": 10}

        result, usage = generate_unified(
            self.profile, self.task, self.root, self.context, transport
        )
        self.assertEqual(result["sections"]["search_profile"]["status"], "valid")
        self.assertEqual(result["sections"]["requirements"]["status"], "invalid")
        self.assertEqual(result["sections"]["requirements"]["candidate"], bad)
        self.assertIsNone(result["sections"]["requirements"]["value"])
        self.assertEqual(
            result["sections"]["student_experience"]["status"], "insufficient_evidence"
        )
        self.assertEqual(result["model_id"], "test@" + "a" * 40)
        self.assertEqual(usage["completion_tokens"], 20)
        self.assertEqual(
            result["source_requirements"], self.root["original_requirements"]
        )

    def test_local_lookup_and_correction_share_one_conversation(self):
        replies = [
            {
                "search_profile": {**self.search, "search_phrases": ["premature"]},
                "requirements": self.requirements,
                "student_experience": self.experience,
                "lookups": [{"course_id": "COMPSCI 200", "from_course": "COMPSCI 300"}],
            },
            {
                "search_profile": self.search,
                "requirements": self.requirements,
                "student_experience": self.experience,
                "lookups": [],
            },
        ]

        def transport(profile, task, messages, allow_lookup):
            if len(replies) == 1:
                self.assertIn("COMPSCI 200", messages[-1]["content"])
            return replies.pop(0), {}

        result, _ = generate_unified(
            self.profile, self.task, self.root, self.context, transport
        )
        self.assertEqual(
            result["provenance"]["dependencies"],
            {"COMPSCI 200": self.context.fingerprint("COMPSCI 200")},
        )
        self.assertEqual(result["sections"]["requirements"]["status"], "valid")
        self.assertEqual(
            result["sections"]["search_profile"]["value"]["search_phrases"],
            self.search["search_phrases"],
        )
        self.assertFalse(replies)

    def test_lookup_depth_cycles_missing_and_budget(self):
        self.lookup.get_course("COMPSCI 200", "COMPSCI 300")
        self.assertTrue(
            self.lookup.get_course("COMPSCI 300", "COMPSCI 200")["already_provided"]
        )
        self.lookup.get_course("COMPSCI 100", "COMPSCI 200")
        self.assertIn("error", self.lookup.get_course("COMPSCI 400", "COMPSCI 100"))
        self.lookup.get_course("COMPSCI 999", "COMPSCI 300")
        old = self.lookup.dependencies["COMPSCI 999"]
        self.context.courses["COMPSCI 999"] = course("COMPSCI 999")
        self.assertNotEqual(old, self.context.fingerprint("COMPSCI 999"))
        self.lookup.get_course("COMPSCI 400", "COMPSCI 300")
        self.assertIn(
            "budget", self.lookup.get_course("COMPSCI 100", "COMPSCI 300")["error"]
        )

    def test_background_cannot_become_taught_content_or_formal_requirement(self):
        self.lookup.get_course("COMPSCI 400", "COMPSCI 300")
        self.search["summary"]["evidence"][0]["course_id"] = "COMPSCI 400"
        with self.assertRaisesRegex(ValueError, "Taught content"):
            validate_section(
                "search_profile", self.search, self.task, self.root, self.lookup
            )
        self.root["description"] = "Recommended: COMPSCI 400."
        self.root["requirements_text"] = "Graduate/professional standing"
        value = {
            "status": "parsed",
            "root": "n",
            "notes": [],
            "nodes": [
                {
                    "id": "n",
                    "kind": "course",
                    "children": [],
                    "condition": None,
                    "evidence": "Graduate/professional standing",
                    "course": {
                        "subjects": ["COMPSCI"],
                        "course_number": 400,
                        "timing": "prior",
                        "minimum_grade": None,
                    },
                }
            ],
        }
        with self.assertRaisesRegex(ValueError, "absent from the source links"):
            validate_section("requirements", value, self.task, self.root, self.lookup)

    def test_sentiment_requires_root_reviews_and_keeps_attribution(self):
        value = {
            "status": "supported",
            "themes": [
                {
                    "aspect": "projects",
                    "sentiment": "positive",
                    "summary": "Projects were useful.",
                    "review_ids": ["r1"],
                }
            ],
        }
        with self.assertRaises(ValueError):
            validate_section(
                "student_experience", value, self.task, self.root, self.lookup
            )
        self.root["reviews"] = [
            {
                "id": "r1",
                "course_id": "COMPSCI 300",
                "comment": "Projects were useful.",
                "date": "2025-05-01",
                "instructor_id": "i1",
                "source_url": "https://example.com/review",
            }
        ]
        result = validate_section(
            "student_experience", value, self.task, self.root, self.lookup
        )
        self.assertEqual(result["value"]["themes"][0]["evidence_count"], 1)
        self.assertEqual(
            result["value"]["themes"][0]["evidence"][0]["instructor_id"], "i1"
        )
        self.assertNotIn("evidence_count", value["themes"][0])

    def test_display_normalization_preserves_original_input(self):
        raw = r"COMP\xa0SCI\xa0300"
        self.assertEqual(text_view(raw), "COMP SCI 300")
        self.assertEqual(raw, r"COMP\xa0SCI\xa0300")
