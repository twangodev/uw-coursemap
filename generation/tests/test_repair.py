"""Native repair conversations retain accepted sections and rejected attempts."""

import copy
import json
import unittest

import test_unified
from uw_coursemap.repair import generate_repair
from uw_coursemap.unified import validate_section


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.fixture = test_unified.UnifiedTests()
        self.fixture.setUp()
        f = self.fixture
        self.task = {**f.task, "repair_turns": 3, "repair_mode": "conversation_v1"}
        self.previous = {
            "course_id": f.root["course_id"],
            "model": "test",
            "model_revision": "a" * 40,
            "sections": {
                "search_profile": validate_section(
                    "search_profile", f.search, f.task, f.root, f.lookup
                ),
                "requirements": {
                    "status": "invalid",
                    "candidate": {**f.requirements, "root": "missing"},
                    "value": None,
                    "error": "Missing root node",
                },
                "student_experience": {
                    "status": "insufficient_evidence",
                    "value": f.experience,
                },
            },
            "provenance": {"worker_version": 10, "dependencies": {}, "tool_calls": []},
        }
        self.payload = {
            **f.root,
            "repair_seed": {"job_id": "parent", "output": self.previous},
        }

    def test_native_conversation_requeues_errors_without_touching_accepted_sections(
        self,
    ):
        original = copy.deepcopy(self.previous)
        calls = []
        f = self.fixture

        def transport(profile, task, messages, allow_lookup):
            calls.append(copy.deepcopy(messages))
            self.assertTrue(profile["thinking"])
            self.assertFalse(allow_lookup)
            self.assertEqual(messages[-1]["role"], "user")
            self.assertIn(
                "requirements", json.loads(messages[-1]["content"])["validation_errors"]
            )
            return {
                "lookups": [],
                "search_profile": {"do_not_accept": True},
                "requirements": {**f.requirements, "root": "still-missing"}
                if len(calls) == 1
                else f.requirements,
                "student_experience": None,
            }, {"completion_tokens": 10}

        output, usage = generate_repair(
            f.profile, self.task, self.payload, f.context, transport
        )
        self.assertEqual(len(calls), 2)
        self.assertEqual(
            [m["role"] for m in calls[1]],
            ["system", "user", "assistant", "user", "assistant", "user"],
        )
        self.assertEqual(
            json.loads(calls[1][-2]["content"])["requirements"]["root"], "still-missing"
        )
        self.assertEqual(output["sections"]["requirements"]["status"], "valid")
        self.assertEqual(
            output["sections"]["search_profile"], original["sections"]["search_profile"]
        )
        self.assertEqual(self.previous, original)
        self.assertEqual(usage["completion_tokens"], 20)
        self.assertEqual(output["provenance"]["repair_parent_job"], "parent")
        self.assertEqual(
            output["provenance"]["retained_sections"],
            ["search_profile", "student_experience"],
        )

    def test_repair_is_bounded_and_preserves_last_rejected_candidate(self):
        f = self.fixture
        calls = []

        def transport(*args):
            calls.append(1)
            return {"requirements": {**f.requirements, "root": "missing"}}, {}

        output, _ = generate_repair(
            f.profile, self.task, self.payload, f.context, transport
        )
        self.assertEqual(len(calls), 3)
        self.assertEqual(output["sections"]["requirements"]["status"], "invalid")
        self.assertEqual(
            output["sections"]["requirements"]["candidate"]["root"], "missing"
        )
        self.assertEqual(len(output["provenance"]["repair_conversation"]), 9)

    def test_failed_request_is_retried_without_fabricating_assistant_answer(self):
        f = self.fixture
        calls = []

        def transport(*args):
            calls.append(copy.deepcopy(args[2]))
            if len(calls) == 1:
                raise ValueError("Truncated output")
            return {"requirements": f.requirements}, {}

        output, _ = generate_repair(
            f.profile, self.task, self.payload, f.context, transport
        )
        self.assertEqual(len(calls[0]), len(calls[1]))
        self.assertIn("Truncated output", calls[1][-1]["content"])
        self.assertEqual(output["sections"]["requirements"]["status"], "valid")

    def test_source_or_dependency_change_blocks_repair(self):
        f = self.fixture
        f.context.courses["COMPSCI 300"] = {**f.root, "description": "Changed"}
        with self.assertRaisesRegex(ValueError, "source context"):
            generate_repair(f.profile, self.task, self.payload, f.context)
