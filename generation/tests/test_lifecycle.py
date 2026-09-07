"""Recovery and isolation guarantees for source snapshots and enrichment."""

import json
import sqlite3
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import test_pipeline
from uw_coursemap.cli import code_hash
from uw_coursemap.jobs import Jobs, generate
from uw_coursemap.lifecycle import scrape, release, build
from uw_coursemap.models import canonical
from uw_coursemap.profiles import ModelProfile, load_profile, lock_profiles
from uw_coursemap.release import verify_release, publish
from uw_coursemap.store import Store, SOURCES


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.fixture = test_pipeline.PipelineTests()
        self.fixture.setUp()
        self.store = self.fixture.store
        self.run = self.fixture.run
        self.root = self.store.root
        self.fixture.seed()
        self.profile = ModelProfile(
            model="test/model", revision="a" * 40, base_url="http://127.0.0.1:8003/v1"
        )
        self.task = self.root / "task.json"
        self.task.write_text(
            canonical(
                {
                    "name": "test",
                    "version": 1,
                    "prompt": "Ground in source",
                    "schema": {
                        "type": "object",
                        "required": ["summary"],
                        "properties": {"summary": {"type": "string"}},
                        "additionalProperties": False,
                    },
                }
            )
        )

    def tearDown(self):
        self.fixture.tearDown()

    def core(self):
        with self.store.db:
            self.store.db.execute("DELETE FROM observations WHERE source='instructors'")
            self.store.db.execute("DELETE FROM artifacts")
            self.store.db.execute(
                "UPDATE stages SET status='pending' WHERE stage IN ('instructors','derive','export')"
            )
            self.store.db.execute(
                "UPDATE runs SET config_json=? WHERE run_id=?",
                (
                    canonical(
                        {
                            "workflow": "snapshot-v1",
                            "code_hash": code_hash(),
                            "sources": list(SOURCES[:3]),
                        }
                    ),
                    self.run,
                ),
            )
        return scrape(self.store, self.run)

    def create_job(self, jobs, run=None):
        with patch("uw_coursemap.jobs.load_profile", return_value=self.profile):
            return jobs.create(
                run or self.run, "unused", "enrichment", self.task, limit=0
            )

    def test_source_only_release_and_publish_during_scrape_lock(self):
        with patch(
            "huggingface_hub.HfApi",
            side_effect=AssertionError("No model metadata needed"),
        ):
            self.core()
            before = self.store.input_hash(self.run)
            with self.store.lock():
                readonly = Store(self.root, readonly=True)
                try:
                    target = release(readonly, self.run)
                    manifest = verify_release(target)
                    self.assertFalse(manifest["website_included"])
                    self.assertEqual(manifest["tables"]["courses"], 1)
                    self.assertGreater(manifest["tables"]["meetings"], 0)
                    self.assertEqual(release(readonly, self.run), target)
                    hub = test_pipeline.FakeHub(self.root)
                    result = publish(
                        readonly, target.name, "owner/data", hub, hub.download
                    )
                    self.assertIn("revision", result)
                    with self.assertRaises(sqlite3.OperationalError):
                        readonly.db.execute("DELETE FROM runs")
                finally:
                    readonly.close()
        self.assertEqual(self.store.input_hash(self.run), before)
        self.assertIsNone(self.store.run(self.run)["revision"])
        self.assertEqual(self.store.stage_status(self.run, "derive"), "pending")

    def test_failed_source_does_not_block_other_sources_and_resumes(self):
        with self.store.db:
            self.store.db.execute("UPDATE stages SET status='pending'")
            self.store.db.execute(
                "UPDATE runs SET config_json=?",
                (
                    canonical(
                        {
                            "workflow": "snapshot-v1",
                            "code_hash": code_hash(),
                            "sources": list(SOURCES[:3]),
                        }
                    ),
                ),
            )
        called = []

        def worker(store, run, source):
            called.append(source)
            if source == "madgrades":
                raise RuntimeError("unavailable")
            store.stage(run, source, "complete")

        with patch("uw_coursemap.cli.execute_source", side_effect=worker):
            with self.assertRaisesRegex(RuntimeError, "madgrades"):
                scrape(self.store, self.run)
        self.assertEqual(called, list(SOURCES[:3]))
        called.clear()

        def resume(store, run, source):
            called.append(source)
            store.stage(run, source, "complete")

        with patch("uw_coursemap.cli.execute_source", side_effect=resume):
            scrape(self.store, self.run)
        self.assertEqual(called, ["madgrades"])

    def test_enrichment_failure_resume_cache_and_explicit_selection(self):
        self.core()
        jobs = Jobs(self.root)
        try:
            job = self.create_job(jobs)
            with self.assertRaises(RuntimeError):
                jobs.run(
                    job,
                    worker=lambda *args: (_ for _ in ()).throw(
                        ValueError("bad output")
                    ),
                )
            self.assertEqual(
                jobs.db.execute(
                    "SELECT error FROM results WHERE job_id=?", (job,)
                ).fetchone()[0],
                "ValueError: bad output",
            )
            with self.assertRaisesRegex(ValueError, "completed enrichment"):
                release(self.store, self.run, enrichment_ids=[job])
            calls = []

            def worker(*args):
                calls.append(args)
                return {"summary": "Grounded summary"}, {"completion_tokens": 3}

            self.assertEqual(jobs.run(job, worker)["status"], "complete")
            jobs.run(job, worker)
            self.assertEqual(len(calls), 1)
            path = release(self.store, self.run, enrichment_ids=[job])
            manifest = verify_release(path)
            self.assertEqual(manifest["tables"]["course_enrichments"], 1)
            with sqlite3.connect(path / "coursemap.sqlite") as db:
                spec = db.execute("SELECT spec_json FROM enrichment_jobs").fetchone()[0]
                self.assertNotIn("127.0.0.1", spec)
                self.assertFalse(db.execute("PRAGMA foreign_key_check").fetchall())
            other = self.store.new_run("1272", {})
            self.fixture.seed(other)
            self.store.finish(other)
            reused = self.create_job(jobs, other)
            jobs.run(reused, worker)
            self.assertEqual(
                len(calls),
                1,
                "unchanged courses reuse validated outputs across snapshots",
            )
            task = json.loads(self.task.read_text())
            task["version"] = 2
            self.task.write_text(canonical(task))
            changed = self.create_job(jobs, other)
            jobs.run(changed, worker)
            self.assertEqual(len(calls), 2, "task changes invalidate cached outputs")
        finally:
            jobs.close()

    def test_unified_dependency_cache_and_dataset_sections(self):
        from pathlib import Path
        from uw_coursemap.course_context import CourseContext

        task = (
            Path(__file__).resolve().parents[2]
            / "inference/tasks/course_enrichment.json"
        )
        jobs = Jobs(self.root)
        calls = []
        runs = []
        try:
            for description in [
                "First prerequisite description",
                "Changed prerequisite description",
                "Changed prerequisite description",
            ]:
                run = self.store.new_run("1272", {})
                self.fixture.seed(run)
                dependency = self.store.records(run, "courses")["COMPSCI 300"].copy()
                dependency["course_reference"] = {
                    "subjects": ["COMPSCI"],
                    "course_number": 200,
                }
                dependency["description"] = description
                self.store.put(
                    run,
                    "catalog",
                    {
                        "kind": "courses",
                        "key": "COMPSCI 200",
                        "source_url": "https://guide.wisc.edu/courses/comp_sci/",
                        "payload": dependency,
                    },
                )
                self.store.finish(run)
                context = CourseContext(self.store, run)
                with patch("uw_coursemap.jobs.load_profile", return_value=self.profile):
                    job = jobs.create(
                        run, "unused", "unified", task, course_ids=["CS 300"]
                    )

                def worker(*args):
                    calls.append(run)
                    return {
                        "model": self.profile.model,
                        "model_revision": self.profile.revision,
                        "sections": {
                            "search_profile": {
                                "status": "valid",
                                "value": {"summary": "fixture"},
                            },
                            "requirements": {
                                "status": "invalid",
                                "value": None,
                                "candidate": {"root": "missing"},
                                "error": "Missing root",
                            },
                        },
                        "provenance": {
                            "dependencies": {
                                "COMPSCI 200": context.fingerprint("COMPSCI 200")
                            }
                        },
                    }, {}

                self.assertEqual(jobs.run(job, worker)["status"], "complete")
                runs.append(run)
            self.assertEqual(calls, runs[:2])
            value = json.loads(
                jobs.db.execute(
                    "SELECT output_json FROM results WHERE job_id=?", (job,)
                ).fetchone()[0]
            )
            self.assertEqual(value["provenance"]["generated_from_snapshot"], runs[1])
            path = release(self.store, run, enrichment_ids=[job])
            manifest = verify_release(path)
            self.assertEqual(manifest["tables"]["enrichment_sections"], 2)
            self.assertIn(self.profile.served_model, (path / "README.md").read_text())
            with sqlite3.connect(path / "coursemap.sqlite") as db:
                rows = db.execute(
                    "SELECT section,status,model,model_revision,value_json,candidate_json FROM enrichment_sections ORDER BY section"
                ).fetchall()
            self.assertEqual(
                rows[0][:4],
                ("requirements", "invalid", self.profile.model, self.profile.revision),
            )
            self.assertIsNone(rows[0][4])
            self.assertEqual(json.loads(rows[0][5]), {"root": "missing"})
            self.assertEqual(rows[1][1], "valid")
        finally:
            jobs.close()

    def test_partial_resume_only_retries_failed_courses(self):
        original = self.store.records(self.run, "courses")["COMPSCI 300"]
        copied = json.loads(canonical(original))
        copied["course_reference"]["course_number"] = 301
        self.store.put(
            self.run,
            "catalog",
            {
                "kind": "courses",
                "key": "COMPSCI 301",
                "payload": copied,
                "source_url": "https://example.org",
            },
        )
        self.core()
        jobs = Jobs(self.root)
        try:
            job = self.create_job(jobs)
            calls = []

            def worker(profile, task, payload):
                number = payload["course_reference"]["course_number"]
                calls.append(number)
                if number == 301:
                    raise ValueError("failed")
                return {"summary": "OK"}, {}

            with self.assertRaises(RuntimeError):
                jobs.run(job, worker)

            def retry(profile, task, payload):
                calls.append(payload["course_reference"]["course_number"])
                return {"summary": "OK"}, {}

            jobs.run(job, retry)
            self.assertEqual(calls.count(300), 1)
            self.assertEqual(calls.count(301), 2)
        finally:
            jobs.close()

    def test_build_failure_recovers_copied_snapshot_without_mutating_source(self):
        self.core()
        before = self.store.input_hash(self.run)
        profile = self.profile.model_copy(update={"runner": "pooling"})
        with (
            patch("uw_coursemap.profiles.load_profile", return_value=profile),
            patch("uw_coursemap.derive.derive", side_effect=RuntimeError("offline")),
        ):
            with self.assertRaises(RuntimeError):
                build(self.root, self.run, "unused")
        directory = next((self.root / "builds").glob("build-*"))
        state = self.store.get_artifact(self.run, "source_state")

        def complete(store, run):
            store.artifact(run, "graph", state, store.input_hash(run), {})

        with (
            self.store.lock(),
            patch("uw_coursemap.derive.derive", side_effect=complete),
        ):
            meta = build(self.root, self.run, build_id=directory.name)
        self.assertEqual(meta["run_id"], directory.name)
        self.assertEqual(self.store.input_hash(self.run), before)
        with patch(
            "uw_coursemap.derive.derive",
            side_effect=AssertionError("reran completed build"),
        ):
            build(self.root, self.run, build_id=directory.name)
        # Recover interruption between the database commit and metadata rename.
        (directory / "build.json").unlink()
        with patch("uw_coursemap.profiles.load_profile", return_value=profile):
            self.assertEqual(build(self.root, self.run, "unused"), meta)
        with sqlite3.connect(directory / "pipeline.sqlite") as db:
            self.assertEqual(db.execute("SELECT count(*) FROM runs").fetchone()[0], 1)

    def test_generation_rejects_truncation_schema_and_false_evidence(self):
        task = json.loads(self.task.read_text())
        task["schema"] = {"type": "object"}
        task["evidence_fields"] = ["topics"]
        for finish, content in [
            ("length", "{}"),
            ("stop", "not json"),
            ("stop", '{"topics":[{"evidence":"invented"}]}'),
        ]:
            with self.subTest(finish=finish, content=content):
                result = {
                    "model": self.profile.served_model,
                    "choices": [
                        {"finish_reason": finish, "message": {"content": content}}
                    ],
                }
                response = SimpleNamespace(
                    raise_for_status=lambda: None, json=lambda: result
                )
                with (
                    patch(
                        "uw_coursemap.jobs.requests.post", return_value=response
                    ) as request,
                    patch("uw_coursemap.jobs.time.sleep"),
                ):
                    with self.assertRaises((ValueError, KeyError)):
                        generate(
                            self.profile.model_dump(),
                            task,
                            {"description": "Actual source"},
                        )
                    self.assertEqual(request.call_count, 3)

    def test_offline_model_fails_before_scheduling_courses(self):
        import requests

        self.core()
        jobs = Jobs(self.root)
        try:
            job = self.create_job(jobs)
            with (
                patch(
                    "uw_coursemap.jobs.requests.get",
                    side_effect=requests.ConnectionError,
                ),
                patch("uw_coursemap.jobs.requests.post") as inference,
            ):
                with self.assertRaisesRegex(
                    RuntimeError, "Inference server unavailable"
                ):
                    jobs.run(job)
                inference.assert_not_called()
            self.assertEqual(jobs.status(job)["counts"], {"pending": 1})
        finally:
            jobs.close()

    def test_http_limits_are_configurable_and_keep_backoff(self):
        from uw_coursemap.crawl import http_settings

        settings = http_settings({})
        self.assertEqual(settings["CONCURRENT_REQUESTS"], 32)
        self.assertEqual(settings["CONCURRENT_REQUESTS_PER_DOMAIN"], 16)
        self.assertTrue(settings["AUTOTHROTTLE_ENABLED"])
        self.assertEqual(settings["AUTOTHROTTLE_MAX_DELAY"], 60)
        custom = http_settings(
            {
                "http": {
                    "concurrency": 12,
                    "per_domain": 6,
                    "target_concurrency": 3,
                    "download_delay": 0.2,
                }
            }
        )
        self.assertEqual(custom["CONCURRENT_REQUESTS_PER_DOMAIN"], 6)
        self.assertEqual(custom["DOWNLOAD_DELAY"], 0.2)
        for limits in [
            {"concurrency": 8, "per_domain": 16},
            {"target_concurrency": 0},
            {"download_delay": -1},
        ]:
            with self.assertRaises(ValueError):
                http_settings({"http": limits})

    def test_historical_crosslisting_ambiguity_preserves_raw_grades(self):
        from uw_coursemap.derive import reconcile, encode_state

        course = self.store.records(self.run, "courses")["COMPSCI 300"]
        course["course_reference"]["subjects"] = ["MUSIC"]
        self.store.put(
            self.run,
            "catalog",
            {
                "kind": "courses",
                "key": "MUSIC 300",
                "payload": course,
                "source_url": "https://example.org/catalog",
            },
        )
        key, grades = next(iter(self.store.records(self.run, "grades").items()))
        grades["course_reference"]["subjects"] = ["COMPSCI", "MUSIC"]
        self.store.put(
            self.run,
            "madgrades",
            {
                "kind": "grades",
                "key": key,
                "payload": grades,
                "source_url": "https://example.org/grades",
            },
        )
        state = encode_state(*reconcile(self.store, self.run))
        self.assertIn(key, state["unmatched"]["grades"])
        self.assertEqual(
            state["unmatched"]["ambiguous_grades"][key], ["COMPSCI 300", "MUSIC 300"]
        )
        self.assertEqual(self.store.records(self.run, "grades")[key], grades)
        self.assertIsNone(state["courses"]["COMPSCI 300"]["cumulative_grade_data"])

    def test_task_projections_exclude_existing_parser_output(self):
        self.core()
        task = json.loads(self.task.read_text())
        task["input_fields"] = {
            "requirements_text": "prerequisites.prerequisites_text",
            "linked_courses": "prerequisites.course_references",
        }
        self.task.write_text(canonical(task))
        jobs = Jobs(self.root)
        try:
            job = self.create_job(jobs)
            payload = json.loads(
                jobs.db.execute(
                    "SELECT input_json FROM results WHERE job_id=?", (job,)
                ).fetchone()[0]
            )
            self.assertEqual(set(payload), {"requirements_text", "linked_courses"})
            self.assertIsInstance(payload["requirements_text"], str)
            self.assertIsInstance(payload["linked_courses"], list)
        finally:
            jobs.close()

    def test_profiles_lock_shared_by_client_and_server(self):
        path = self.root / "models.toml"
        path.write_text(
            '[profiles.test]\nmodel="test/model"\nbase_url="http://127.0.0.1:8003/v1"\n'
        )
        output = self.root / "locked.json"
        with patch("huggingface_hub.HfApi") as hub:
            hub.return_value.model_info.return_value.sha = "b" * 40
            lock_profiles(path, ["test"], output)
        profile = load_profile(output, "test", resolve=False)
        self.assertEqual(profile.revision, "b" * 40)
        self.assertEqual(profile.served_model, "test/model@" + "b" * 40)
