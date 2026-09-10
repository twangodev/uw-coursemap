import json
from pathlib import Path
import tempfile
import unittest

from uwcourses.models import digest
from uwcourses.tasks import load_task


class TaskTests(unittest.TestCase):
    def test_grounding_assets_are_frozen_and_cycles_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            main = root / "main.json"
            check = root / "check.json"
            main.write_text(json.dumps({"grounding_task_file": "check.json"}))
            check.write_text(
                json.dumps({"prompt": "Check evidence", "schema": {"type": "object"}})
            )
            frozen = load_task(main)
            self.assertEqual(frozen["grounding_task"]["prompt"], "Check evidence")
            check.write_text(
                json.dumps({"prompt": "Updated check", "schema": {"type": "object"}})
            )
            self.assertNotEqual(digest(frozen), digest(load_task(main)))
            check.write_text(json.dumps({"grounding_task_file": "main.json"}))
            with self.assertRaisesRegex(ValueError, "Cyclic"):
                load_task(main)

    def test_relative_assets_are_frozen_and_content_changes_affect_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "prompt.md").write_text("First instructions.\n")
            (root / "schema.json").write_text('{"type":"object"}')
            manifest = root / "task.json"
            manifest.write_text(
                json.dumps(
                    {
                        "name": "test",
                        "version": 1,
                        "prompt_files": ["prompt.md"],
                        "schema_file": "schema.json",
                    }
                )
            )
            frozen = load_task(manifest)
            encoded = json.dumps(frozen)
            self.assertEqual(frozen["prompt"], "First instructions.")
            self.assertNotIn("prompt_files", frozen)
            self.assertNotIn("schema_file", frozen)
            (root / "prompt.md").write_text("Revised instructions.")
            self.assertNotEqual(digest(frozen), digest(load_task(manifest)))
            self.assertEqual(json.dumps(frozen), encoded)
            previous = load_task(manifest)
            (root / "schema.json").write_text('{"type":"string"}')
            self.assertNotEqual(digest(previous), digest(load_task(manifest)))

    def test_inline_tasks_remain_supported_and_ambiguous_sources_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "task.json"
            task = {"prompt": "Hello", "schema": {"type": "object"}}
            path.write_text(json.dumps(task))
            self.assertEqual(load_task(path), task)
            for extra in (
                {"prompt_files": ["missing.md"]},
                {"schema_file": "missing.json"},
            ):
                path.write_text(json.dumps({**task, **extra}))
                with self.assertRaisesRegex(ValueError, "not both"):
                    load_task(path)

    def test_bundled_tasks_resolve_and_runtime_prompt_does_not_accumulate(self):
        import jsonschema
        from uwcourses.agents import native_prompt

        root = Path(__file__).resolve().parents[2] / "inference/tasks"
        for path in root.glob("*.json"):
            with self.subTest(task=path.name):
                task = load_task(path)
                self.assertTrue(task["prompt"].strip())
                jsonschema.Draft202012Validator.check_schema(task["schema"])
                wrapped = native_prompt(task)
                self.assertEqual(native_prompt({**task, "prompt": wrapped}), wrapped)
