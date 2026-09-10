import copy
import json
from pathlib import Path
import unittest

import jsonschema

from uwcourses.requirements import restore_quotes, validate_graph, graph_diagnostics
from uwcourses.requirements_eval import expression, matches, normalize
from uwcourses.tasks import load_task


class RequirementsTests(unittest.TestCase):
    def setUp(self):
        self.task = load_task(
            Path(__file__).resolve().parents[2] / "inference/tasks/requirements.json"
        )
        self.payload = {
            "requirements_text": "MATH 221 or consent of instructor",
            "linked_courses": [{"subjects": ["MATH"], "course_number": 221}],
        }
        self.value = {
            "status": "parsed",
            "root": "r",
            "notes": [],
            "nodes": [
                {
                    "id": "r",
                    "kind": "any",
                    "children": ["a", "b"],
                    "course": None,
                    "condition": None,
                    "evidence": "MATH 221 or consent of instructor",
                },
                {
                    "id": "a",
                    "kind": "course",
                    "children": [],
                    "course": {
                        "subjects": ["MATH"],
                        "course_number": 221,
                        "timing": "prior",
                        "minimum_grade": None,
                    },
                    "condition": None,
                    "evidence": "MATH 221",
                },
                {
                    "id": "b",
                    "kind": "condition",
                    "children": [],
                    "course": None,
                    "condition": "consent of instructor",
                    "evidence": "consent of instructor",
                },
            ],
        }

    def test_whole_source_condition_is_restored_without_inventing_text(self):
        payload = {
            "requirements_text": "Graduate/professional standing",
            "linked_courses": [],
        }
        value = {
            "status": "parsed",
            "root": "n",
            "notes": [],
            "nodes": [
                {
                    "id": "n",
                    "kind": "condition",
                    "children": [],
                    "course": None,
                    "condition": None,
                    "evidence": "Graduate/professional standing.",
                }
            ],
        }
        restore_quotes(value, payload)
        validate_graph(value, payload)
        self.assertEqual(value["nodes"][0]["condition"], payload["requirements_text"])
        for quote in ["Graduate", "Undergraduate standing"]:
            value["nodes"][0].update(condition=None, evidence=quote)
            restore_quotes(value, payload)
            self.assertIsNone(value["nodes"][0]["condition"])
            with self.assertRaises(ValueError):
                validate_graph(value, payload)

    def test_unlinked_numeric_alternative_cannot_be_silently_dropped(self):
        self.payload["requirements_text"] += " or 171"
        with self.assertRaisesRegex(ValueError, "missing from leaf conditions: 171"):
            validate_graph(self.value, self.payload)
        self.value["nodes"][0]["children"].append("unlinked")
        self.value["nodes"].append(
            {
                "id": "unlinked",
                "kind": "condition",
                "children": [],
                "course": None,
                "condition": "171",
                "evidence": "171",
            }
        )
        self.value["status"] = "needs_review"
        self.value["notes"] = ["Unlinked course number preserved verbatim."]
        validate_graph(self.value, self.payload)

    def test_supported_expression_preserves_course_and_noncourse_alternative(self):
        jsonschema.Draft202012Validator(self.task["schema"]).validate(self.value)
        validate_graph(self.value, self.payload)

    def test_rejects_invented_evidence_courses_and_broken_graphs(self):
        bad = []
        for field, value in [
            ("evidence", "MATH 222"),
            (
                "course",
                {
                    "subjects": ["MATH"],
                    "course_number": 222,
                    "timing": "prior",
                    "minimum_grade": None,
                },
            ),
        ]:
            item = copy.deepcopy(self.value)
            item["nodes"][1][field] = value
            bad.append(item)
        item = copy.deepcopy(self.value)
        item["nodes"][0]["children"] = ["r", "b"]
        bad.append(item)
        item = copy.deepcopy(self.value)
        item["nodes"][0]["children"] = ["a", "missing"]
        bad.append(item)
        item = copy.deepcopy(self.value)
        item["root"] = "a"
        bad.append(item)
        for value in bad:
            with self.assertRaises(ValueError):
                validate_graph(value, self.payload)

    def test_none_requires_explicit_no_requirements_and_ambiguity_is_reported(self):
        value = {"status": "none", "root": None, "nodes": [], "notes": []}
        validate_graph(value, {"requirements_text": "None"})
        with self.assertRaises(ValueError):
            validate_graph(value, self.payload)
        value.update(status="needs_review", notes=["Grouping is ambiguous"])
        validate_graph(value, self.payload)

    def test_generation_grammar_keeps_full_validation_contract(self):
        from uwcourses.jobs import generation_schema

        original = {
            "type": "object",
            "properties": {
                "values": {
                    "type": "array",
                    "uniqueItems": True,
                    "items": {"type": "string"},
                }
            },
        }
        grammar = generation_schema(original)
        self.assertNotIn("uniqueItems", grammar["properties"]["values"])
        self.assertTrue(original["properties"]["values"]["uniqueItems"])
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate({"values": ["duplicate", "duplicate"]}, original)

    def test_whitespace_quotes_restore_source_without_changing_words(self):
        payload = {
            **self.payload,
            "requirements_text": "MATH\u00a0221 or consent\t of instructor",
        }
        restore_quotes(self.value, payload)
        validate_graph(self.value, payload)
        self.assertEqual(self.value["nodes"][1]["evidence"], "MATH\u00a0221")
        self.assertEqual(self.value["nodes"][2]["condition"], "consent\t of instructor")
        self.value["nodes"][1]["evidence"] = "MATH 222"
        restore_quotes(self.value, payload)
        with self.assertRaises(ValueError):
            validate_graph(self.value, payload)

    def test_case_and_terminal_period_resolve_to_literal_source(self):
        self.value["nodes"][2]["evidence"] = "Consent of instructor."
        self.value["nodes"][2]["condition"] = "Consent of instructor."
        restore_quotes(self.value, self.payload)
        validate_graph(self.value, self.payload)
        self.assertEqual(self.value["nodes"][2]["condition"], "consent of instructor")
        self.value["nodes"][2]["condition"] = "no consent of instructor"
        restore_quotes(self.value, self.payload)
        with self.assertRaises(ValueError):
            validate_graph(self.value, self.payload)

    def test_feedback_identifies_invented_course_and_missing_condition(self):
        self.value["nodes"][1]["course"]["course_number"] = 0
        self.value["nodes"][2]["condition"] = None
        errors = "\n".join(graph_diagnostics(self.value, self.payload))
        self.assertIn("Never invent course 0", errors)
        self.assertIn("Allowed course references", errors)
        self.assertIn("condition None", errors)
        self.assertIn("consent of instructor", errors)
        with self.assertRaises(ValueError):
            validate_graph(self.value, self.payload)

    def test_standalone_exclusion_cannot_apply_to_only_one_alternative(self):
        clause = "Not open to students with credit for MATH 222"
        payload = copy.deepcopy(self.payload)
        payload["requirements_text"] += ". " + clause + "."
        payload["linked_courses"].append({"subjects": ["MATH"], "course_number": 222})
        course = copy.deepcopy(self.value["nodes"][1])
        course.update(id="excluded", evidence="MATH 222")
        course["course"]["course_number"] = 222
        group = {
            "id": "global",
            "kind": "all",
            "children": ["r", "exclusion"],
            "course": None,
            "condition": None,
            "evidence": payload["requirements_text"],
        }
        negative = {
            "id": "exclusion",
            "kind": "not",
            "children": ["excluded"],
            "course": None,
            "condition": None,
            "evidence": clause,
        }
        self.value["nodes"].extend([course, group, negative])
        self.value["root"] = "global"
        validate_graph(self.value, payload)
        # Incorrectly exempt the course-based path from the global exclusion.
        self.value["root"] = "r"
        self.value["nodes"][0]["children"] = ["a", "global"]
        group["children"] = ["b", "exclusion"]
        with self.assertRaisesRegex(ValueError, "every eligibility alternative"):
            validate_graph(self.value, payload)

    def test_evaluation_detects_grouping_timing_grade_and_status_errors(self):
        case = {
            "expected_status": "parsed",
            "expected_expression": expression(self.value),
        }
        self.assertTrue(matches(case, self.value))
        self.value["nodes"][0]["children"].reverse()
        self.assertTrue(matches(case, self.value))
        for field, replacement in [
            ("timing", "prior_or_concurrent"),
            ("minimum_grade", "C"),
        ]:
            changed = copy.deepcopy(self.value)
            changed["nodes"][1]["course"][field] = replacement
            self.assertFalse(matches(case, changed))
        changed = copy.deepcopy(self.value)
        changed["nodes"][0]["kind"] = "all"
        self.assertFalse(matches(case, changed))
        changed["status"] = "needs_review"
        self.assertFalse(matches(case, changed))

    def test_evaluation_flattens_associative_groups_but_preserves_negation(self):
        a, b, c = ({"condition": name} for name in ("a", "b", "c"))
        self.assertEqual(
            normalize({"all": [a, {"all": [c, b]}]}), normalize({"all": [c, b, a]})
        )
        self.assertNotEqual(
            normalize({"not": [{"any": [a, b]}]}),
            normalize({"any": [{"not": [a]}, {"not": [b]}]}),
        )

    def test_retry_explains_error_and_sends_schema_to_model(self):
        broken = copy.deepcopy(self.value)
        broken["root"] = "missing"

        from pydantic_ai.messages import ModelResponse, TextPart
        from pydantic_ai.models.function import FunctionModel
        from pydantic_ai import ModelMessagesTypeAdapter
        from uwcourses.agents import generate_generic

        calls = []

        def model(messages, info):
            calls.append(ModelMessagesTypeAdapter.dump_json(messages).decode())
            return ModelResponse(
                parts=[TextPart(json.dumps(broken if len(calls) == 1 else self.value))]
            )

        value, _ = generate_generic(
            {"model": "test", "revision": "revision", "max_output_tokens": 4096},
            self.task,
            self.payload,
            FunctionModel(model),
        )
        value.pop("provenance")
        self.assertEqual(value, self.value)
        self.assertEqual(len(calls), 2)
        self.assertIn("Missing requirement root", calls[1])
