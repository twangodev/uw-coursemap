import copy
import json
from pathlib import Path
import unittest

import jsonschema

from uw_coursemap.requirements import validate_graph


class RequirementsTests(unittest.TestCase):
    def setUp(self):
        self.task = json.loads(
            (
                Path(__file__).resolve().parents[2]
                / "inference/tasks/requirements.json"
            ).read_text()
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
        from uw_coursemap.jobs import generation_schema

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
