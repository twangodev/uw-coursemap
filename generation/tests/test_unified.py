import json
from pathlib import Path
import unittest

from uw_coursemap.course_context import CourseLookup, text_view
from uw_coursemap.models import digest
from uw_coursemap.requirements import graph_diagnostics
from uw_coursemap.unified import (
    compare_parsers,
    generate_unified,
    source_quote,
    validate_section,
)

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
        self.task["ast_repair_attempts"] = 2
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
        self.assertEqual(usage["completion_tokens"], 30)
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

    def test_abbreviated_citations_expand_only_ordered_source_fragments(self):
        self.assertEqual(
            source_quote("Programming...objects.", "Programming using objects."),
            "Programming using objects.",
        )
        self.assertIsNone(
            source_quote("objects...Programming", "Programming using objects.")
        )
        self.assertIsNone(
            source_quote("Programming...Java", "Programming using objects.")
        )
        self.search["summary"]["evidence"][0]["quote"] = "Programming...objects."
        result = validate_section(
            "search_profile", self.search, self.task, self.root, self.lookup
        )
        self.assertEqual(
            result["value"]["summary"]["evidence"][0]["quote"],
            "Programming using objects.",
        )
        self.assertEqual(
            result["citation_repairs"][0]["original"]["quote"], "Programming...objects."
        )
        self.assertEqual(
            self.search["summary"]["evidence"][0]["quote"], "Programming...objects."
        )

    def test_legacy_disagreement_flags_review_without_replacing_candidate(self):
        value = {
            "status": "parsed",
            "root": "n",
            "nodes": [
                {
                    "id": "n",
                    "kind": "condition",
                    "children": [],
                    "condition": "Graduate standing",
                    "course": None,
                    "evidence": "Graduate standing",
                }
            ],
            "notes": [],
        }
        section = {"status": "valid", "value": value}
        compare_parsers(section, {"ast": "Graduate standing"})
        self.assertTrue(section["parser_comparison"]["structural_match"])
        compare_parsers(section, {"ast": "Consent of instructor"})
        self.assertEqual(section["status"], "needs_review")
        self.assertFalse(section["parser_comparison"]["structural_match"])
        self.assertEqual(section["value"], value)

    def test_ast_repairs_enable_thinking_and_preserve_accepted_sections(self):
        calls = []
        bad = {**self.requirements, "root": "missing"}

        def transport(profile, task, messages, allow_lookup):
            calls.append(profile.get("thinking", False))
            if len(calls) > 1:
                feedback = json.loads(messages[-1]["content"])
                self.assertEqual(feedback["rejected_requirements"], bad)
                self.assertIn("requirements", feedback["validation_errors"])
                self.assertFalse(allow_lookup)
            return {
                "lookups": [],
                "search_profile": self.search if len(calls) == 1 else None,
                "student_experience": self.experience if len(calls) == 1 else None,
                "requirements": self.requirements if len(calls) == 3 else bad,
            }, {}

        result, _ = generate_unified(
            self.profile, self.task, self.root, self.context, transport
        )
        self.assertEqual(calls, [False, True, True])
        self.assertEqual(result["sections"]["requirements"]["status"], "valid")
        self.assertEqual(result["sections"]["search_profile"]["value"], self.search)
        self.assertEqual(
            [a["thinking"] for a in result["provenance"]["attempts"]], calls
        )
        self.assertEqual(
            result["provenance"]["attempts"][0]["rejected_requirements"], bad
        )

    def test_graph_feedback_collects_quotes_cycles_unreachable_and_exclusions(self):
        node = {
            "id": "n0",
            "kind": "any",
            "children": ["n0", "missing"],
            "evidence": "invented",
            "condition": None,
            "course": None,
        }
        value = {
            "status": "needs_review",
            "root": "n0",
            "notes": ["review"],
            "nodes": [node, {**node, "id": "orphan", "children": []}],
        }
        errors = "\n".join(
            graph_diagnostics(
                value,
                {
                    "requirements_text": "Graduate standing. Not open to students with credit for COMP SCI 367."
                },
            )
        )
        for expected in [
            "evidence",
            "references itself",
            "missing nodes",
            "Cycle",
            "Unreachable nodes: orphan",
            "Missing global exclusion",
            "367",
        ]:
            self.assertIn(expected, errors)

    def test_failed_ast_repair_requests_stop_after_two_and_keep_search(self):
        calls = []

        def transport(profile, task, messages, allow_lookup):
            calls.append(profile.get("thinking", False))
            if len(calls) > 1:
                raise ValueError("Unified output was truncated")
            return {
                "lookups": [],
                "search_profile": self.search,
                "student_experience": self.experience,
                "requirements": {**self.requirements, "root": "missing"},
            }, {}

        result, _ = generate_unified(
            self.profile, self.task, self.root, self.context, transport
        )
        self.assertEqual(calls, [False, True, True])
        self.assertEqual(result["sections"]["requirements"]["status"], "invalid")
        self.assertEqual(result["sections"]["search_profile"]["value"], self.search)
        self.assertIn("truncated", result["provenance"]["attempts"][-1]["error"])

    def test_citation_quote_style_and_title_restore_literal_evidence(self):
        for quote in ["the golden age of Hollywood", "the 'golden age' of Hollywood"]:
            resolved = source_quote(quote, 'the "golden age" of Hollywood')
            self.assertEqual(resolved, 'the "golden age" of Hollywood')
        self.assertIsNone(source_quote("students can enroll", "students cannot enroll"))
        self.assertIsNone(source_quote("students cant enroll", "students can't enroll"))
        self.root["title"] = "FOURTH SEMESTER URDU"
        self.search["summary"]["evidence"][0]["quote"] = self.root["title"]
        result = validate_section(
            "search_profile", self.search, self.task, self.root, self.lookup
        )
        self.assertEqual(result["value"]["summary"]["evidence"][0]["field"], "title")
        self.assertEqual(
            result["citation_repairs"][0]["original"]["field"], "description"
        )

    def test_excluded_courses_cannot_supply_assumed_background(self):
        self.lookup.get_course("COMPSCI 200", "COMPSCI 300")
        self.root["requirements_text"] = (
            "Graduate standing. Not open to students with credit for COMP SCI 200."
        )
        self.search["assumed_background"] = [
            {
                "text": "Prior object-oriented programming",
                "evidence": [
                    {
                        "course_id": "COMPSCI 200",
                        "field": "description",
                        "quote": "Programming using objects.",
                    }
                ],
            }
        ]
        with self.assertRaisesRegex(ValueError, "credit exclusion"):
            validate_section(
                "search_profile", self.search, self.task, self.root, self.lookup
            )
        self.root["requirements_text"] = "COMP SCI 200"
        self.assertEqual(
            validate_section(
                "search_profile", self.search, self.task, self.root, self.lookup
            )["status"],
            "valid",
        )

    def test_clipped_summary_is_rejected(self):
        self.search["summary"]["text"] = "Genomics applications in microbi,"
        with self.assertRaisesRegex(ValueError, "clipped"):
            validate_section(
                "search_profile", self.search, self.task, self.root, self.lookup
            )

    def test_none_legacy_ast_agrees_with_empty_graph(self):
        section = {"status": "valid", "value": self.requirements}
        compare_parsers(section, {"ast": "None"})
        self.assertTrue(section["parser_comparison"]["structural_match"])
        self.assertEqual(section["status"], "valid")

    def test_bulk_defers_ast_while_repairing_search_without_thinking(self):
        self.task["ast_repair_attempts"] = 0
        bad = {**self.requirements, "root": "missing"}
        calls = []

        def transport(profile, task, messages, allow_lookup):
            calls.append(profile.get("thinking", False))
            if len(calls) == 1:
                return {
                    "lookups": [],
                    "search_profile": {
                        **self.search,
                        "summary": {**self.search["summary"], "text": "clipped,"},
                    },
                    "requirements": bad,
                    "student_experience": self.experience,
                }, {}
            feedback = json.loads(messages[-1]["content"])
            self.assertEqual(feedback["sections_needed"], ["search_profile"])
            self.assertEqual(feedback["deferred_sections"], ["requirements"])
            self.assertIsNone(feedback["rejected_requirements"])
            return {
                "lookups": [],
                "search_profile": self.search,
                "requirements": self.requirements,
                "student_experience": None,
            }, {}

        result, _ = generate_unified(
            self.profile, self.task, self.root, self.context, transport
        )
        self.assertEqual(calls, [False, False])
        self.assertEqual(result["sections"]["search_profile"]["status"], "valid")
        self.assertEqual(result["sections"]["requirements"]["candidate"], bad)
        self.assertEqual(result["sections"]["requirements"]["status"], "invalid")
        self.assertEqual(result["provenance"]["ast_repair_attempts"], 0)
