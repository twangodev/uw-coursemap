"""PydanticAI owns tools, retries and message history; validators own acceptance."""

import copy
import json
import unittest

from pydantic_ai import ModelMessagesTypeAdapter
from pydantic_ai.messages import (
    ModelResponse,
    RetryPromptPart,
    TextPart,
    ThinkingPart,
    ToolCallPart,
    ToolReturnPart,
)
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.usage import RequestUsage

import test_unified
from uw_coursemap.agents import generate_unified, generate_repair, generate_generic
from uw_coursemap.unified import validate_section


class AgentTests(unittest.TestCase):
    def setUp(self):
        f = self.fixture = test_unified.UnifiedTests()
        f.setUp()
        self.task = {**f.task, "ast_repair_attempts": 0, "repair_turns": 3}
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
        self.seed = {
            **f.root,
            "repair_seed": {"job_id": "parent", "output": self.previous},
        }

    def response(self, value, **kwargs):
        return ModelResponse(
            parts=[ToolCallPart("submit_sections", value)],
            usage=RequestUsage(input_tokens=10, output_tokens=5),
            **kwargs,
        )

    def test_valid_saved_candidate_is_revalidated_without_inference(self):
        f = self.fixture
        self.previous["sections"]["requirements"]["candidate"] = f.requirements

        def model(*args):
            self.fail("A valid saved candidate should not require another model call")

        output, usage = generate_repair(
            f.profile, self.task, self.seed, f.context, FunctionModel(model)
        )
        self.assertEqual(output["sections"]["requirements"]["status"], "valid")
        self.assertTrue(output["provenance"]["validation_only"])
        self.assertEqual(
            output["provenance"]["revalidated_candidates"], ["requirements"]
        )
        self.assertEqual(usage["requests"], 0)
        self.assertEqual(output["provenance"]["conversation"], [])

    def test_native_repair_uses_model_retry_and_locks_accepted_sections(self):
        f = self.fixture
        calls = []
        original = copy.deepcopy(self.previous)

        def model(messages, info):
            calls.append(copy.deepcopy(messages))
            self.assertEqual(info.model_settings["tool_choice"], ["submit_sections"])
            if len(calls) > 1:
                self.assertTrue(
                    any(
                        isinstance(part, RetryPromptPart)
                        for m in messages
                        for part in m.parts
                    )
                )
                self.assertIn(
                    "missing-again",
                    ModelMessagesTypeAdapter.dump_json(messages).decode(),
                )
            return self.response(
                {
                    "search_profile": {"bad": "ignore"},
                    "requirements": {**f.requirements, "root": "missing-again"}
                    if len(calls) == 1
                    else f.requirements,
                    "student_experience": None,
                }
            )

        output, usage = generate_repair(
            f.profile, self.task, self.seed, f.context, FunctionModel(model)
        )
        self.assertEqual(len(calls), 2)
        self.assertEqual(output["sections"]["requirements"]["status"], "valid")
        self.assertEqual(
            output["sections"]["search_profile"], original["sections"]["search_profile"]
        )
        self.assertEqual(self.previous, original)
        self.assertEqual(usage["completion_tokens"], 10)
        self.assertEqual(output["provenance"]["repair_parent_job"], "parent")
        self.assertEqual(output["provenance"]["orchestrator"]["name"], "pydantic-ai")
        self.assertTrue(output["provenance"]["generation_settings"]["thinking"])
        ModelMessagesTypeAdapter.validate_python(output["provenance"]["conversation"])

    def test_exhausted_native_repair_keeps_last_rejection_and_history(self):
        f = self.fixture
        calls = []

        def model(*args):
            calls.append(1)
            return self.response(
                {"requirements": {**f.requirements, "root": "still-missing"}}
            )

        output, _ = generate_repair(
            f.profile, self.task, self.seed, f.context, FunctionModel(model)
        )
        self.assertEqual(len(calls), 3)
        self.assertEqual(output["sections"]["requirements"]["status"], "invalid")
        self.assertEqual(
            output["sections"]["requirements"]["candidate"]["root"], "still-missing"
        )
        self.assertIsNotNone(output["provenance"]["request_error"])
        self.assertGreater(len(output["provenance"]["conversation"]), 4)

    def test_bulk_defers_ast_and_repairs_search_without_replacing_accepted_data(self):
        f = self.fixture
        calls = []

        def model(*args):
            calls.append(1)
            search = copy.deepcopy(f.search)
            if len(calls) == 1:
                search["summary"]["evidence"][0]["quote"] = "fabricated quote"
            return self.response(
                {
                    "search_profile": search,
                    "requirements": {**f.requirements, "root": "missing"},
                    "student_experience": f.experience,
                }
            )

        output, _ = generate_unified(
            f.profile, self.task, f.root, f.context, FunctionModel(model)
        )
        self.assertEqual(len(calls), 2)
        self.assertEqual(output["sections"]["search_profile"]["status"], "valid")
        self.assertEqual(output["sections"]["requirements"]["status"], "invalid")
        self.assertFalse(any(a["thinking"] for a in output["provenance"]["attempts"]))

    def test_inline_ast_retry_budget_is_respected(self):
        f = self.fixture
        calls = []

        def model(*args):
            calls.append(1)
            return self.response(
                {
                    "search_profile": f.search,
                    "requirements": {**f.requirements, "root": "missing"},
                    "student_experience": f.experience,
                }
            )

        output, _ = generate_unified(
            f.profile,
            {**self.task, "ast_repair_attempts": 1},
            f.root,
            f.context,
            FunctionModel(model),
        )
        self.assertEqual(len(calls), 2)
        self.assertEqual(output["sections"]["requirements"]["status"], "invalid")

    def test_native_tool_call_uses_bounded_snapshot_lookup(self):
        f = self.fixture
        calls = []

        def model(messages, info):
            calls.append(1)
            self.assertEqual(info.function_tools[0].name, "get_course")
            if len(calls) == 1:
                return ModelResponse(
                    parts=[
                        ToolCallPart(
                            "get_course",
                            {"course_id": "COMPSCI 200", "from_course": "COMPSCI 300"},
                        )
                    ]
                )
            self.assertTrue(
                any(isinstance(p, ToolReturnPart) for m in messages for p in m.parts)
            )
            return self.response(
                {
                    "search_profile": f.search,
                    "requirements": f.requirements,
                    "student_experience": f.experience,
                }
            )

        output, _ = generate_unified(
            f.profile, self.task, f.root, f.context, FunctionModel(model)
        )
        self.assertEqual(len(calls), 2)
        self.assertEqual(
            output["provenance"]["dependencies"]["COMPSCI 200"],
            f.context.fingerprint("COMPSCI 200"),
        )
        self.assertEqual(output["sections"]["search_profile"]["status"], "valid")

    def test_thinking_only_truncation_recovers_without_thinking(self):
        f = self.fixture
        calls = []

        def model(messages, info):
            calls.append(info.model_settings)
            if len(calls) == 1:
                return ModelResponse(
                    parts=[ThinkingPart("repeated analysis " * 20)],
                    finish_reason="length",
                )
            self.assertFalse(
                info.model_settings["extra_body"]["chat_template_kwargs"][
                    "enable_thinking"
                ]
            )
            self.assertFalse(
                any(isinstance(p, ThinkingPart) for m in messages for p in m.parts)
            )
            self.assertIn(
                "exhausted the token budget",
                ModelMessagesTypeAdapter.dump_json(messages).decode(),
            )
            return self.response(
                {
                    "requirements": f.requirements,
                    "search_profile": None,
                    "student_experience": None,
                }
            )

        output, _ = generate_repair(
            f.profile, self.task, self.seed, f.context, FunctionModel(model)
        )
        self.assertEqual(len(calls), 2)
        self.assertEqual(output["sections"]["requirements"]["status"], "valid")
        self.assertIsNone(output["provenance"]["request_error"])
        self.assertEqual(len(output["provenance"]["recovery_events"]), 1)
        self.assertEqual(
            output["sections"]["search_profile"],
            self.previous["sections"]["search_profile"],
        )

    def test_chained_repair_retains_previous_direct_recovery_mode(self):
        f = self.fixture
        self.previous["provenance"]["recovery_events"] = [{"thinking": False}]

        def model(messages, info):
            self.assertFalse(
                info.model_settings["extra_body"]["chat_template_kwargs"][
                    "enable_thinking"
                ]
            )
            self.assertEqual(info.model_settings["tool_choice"], ["submit_sections"])
            return self.response({"requirements": f.requirements})

        output, _ = generate_repair(
            f.profile, self.task, self.seed, f.context, FunctionModel(model)
        )
        self.assertEqual(output["sections"]["requirements"]["status"], "valid")

    def test_plain_json_submission_still_gets_domain_validation_and_retry(self):
        f = self.fixture
        calls = []

        def model(*args):
            calls.append(1)
            value = {
                "requirements": {**f.requirements, "status": "parsed"}
                if len(calls) == 1
                else f.requirements
            }
            return ModelResponse(parts=[TextPart(json.dumps(value))])

        output, _ = generate_repair(
            f.profile, self.task, self.seed, f.context, FunctionModel(model)
        )
        self.assertEqual(len(calls), 2)
        self.assertEqual(output["sections"]["requirements"]["status"], "valid")
        self.assertEqual(len(output["provenance"]["attempts"]), 2)

    def test_thinking_truncation_recovery_is_bounded(self):
        f = self.fixture
        calls = []

        def model(*args):
            calls.append(1)
            return ModelResponse(
                parts=[ThinkingPart("unfinished")], finish_reason="length"
            )

        output, _ = generate_repair(
            f.profile, self.task, self.seed, f.context, FunctionModel(model)
        )
        self.assertEqual(len(calls), 2)
        self.assertEqual(output["sections"]["requirements"]["status"], "invalid")
        self.assertIn("Model token limit", output["provenance"]["request_error"])

    def test_truncated_balanced_json_is_not_accepted(self):
        f = self.fixture

        def model(*args):
            return self.response(
                {
                    "search_profile": f.search,
                    "requirements": f.requirements,
                    "student_experience": f.experience,
                },
                finish_reason="length",
            )

        output, _ = generate_unified(
            f.profile, self.task, f.root, f.context, FunctionModel(model)
        )
        self.assertEqual(output["sections"]["search_profile"]["status"], "invalid")
        self.assertTrue(output["provenance"]["request_error"])

    def test_chained_repair_resumes_serialized_native_conversation(self):
        f = self.fixture

        def reject(*args):
            return self.response(
                {"requirements": {**f.requirements, "root": "unresolved"}}
            )

        previous, _ = generate_repair(
            f.profile, self.task, self.seed, f.context, FunctionModel(reject)
        )
        payload = {
            **f.root,
            "repair_seed": {"job_id": "second-parent", "output": previous},
        }

        def accept(messages, info):
            self.assertGreaterEqual(
                len(messages), len(previous["provenance"]["conversation"])
            )
            self.assertIn(
                "unresolved", ModelMessagesTypeAdapter.dump_json(messages).decode()
            )
            return self.response({"requirements": f.requirements})

        output, _ = generate_repair(
            f.profile, self.task, payload, f.context, FunctionModel(accept)
        )
        self.assertEqual(output["sections"]["requirements"]["status"], "valid")
        self.assertEqual(output["provenance"]["repair_parent_job"], "second-parent")

    def test_generic_agent_rejects_truncation_bad_json_and_false_evidence(self):
        from pydantic_ai.exceptions import UnexpectedModelBehavior

        task = {
            "name": "generic",
            "prompt": "Extract quoted topics",
            "schema": {"type": "object"},
            "evidence_fields": ["topics"],
        }
        for finish, content in [
            ("length", "{}"),
            ("stop", "not json"),
            ("stop", '{"topics":[{"evidence":"invented"}]}'),
        ]:
            with self.subTest(finish=finish, content=content):
                calls = []

                def model(*args):
                    calls.append(1)
                    return ModelResponse(
                        parts=[TextPart(content)], finish_reason=finish
                    )

                with self.assertRaises(UnexpectedModelBehavior):
                    generate_generic(
                        {"max_output_tokens": 1024},
                        task,
                        {"description": "Actual source"},
                        FunctionModel(model),
                    )
                self.assertEqual(len(calls), 3)

    def test_changed_source_blocks_repair_before_inference(self):
        f = self.fixture
        f.context.courses["COMPSCI 300"] = {**f.root, "description": "Changed"}
        with self.assertRaisesRegex(ValueError, "Source context"):
            generate_repair(f.profile, self.task, self.seed, f.context)
