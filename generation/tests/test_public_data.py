"""Public contracts: temporal identity, typed data and safe serving projections."""

import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

import pyarrow as pa
import pyarrow.parquet as pq

from uw_coursemap.history import ENRICHMENT_SCHEMA, write_course
from uw_coursemap.models import canonical
from uw_coursemap.public_data import (
    SCHEMAS,
    catalog_record,
    dataset_card,
    export_public,
    search_ids,
    write_public,
    write_rows,
    selected_enrichments,
)
from uw_coursemap.release import PUBLIC_SCHEMA, write_parquet


class PublicDataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.database = self.root / "archive.sqlite"
        self.db = sqlite3.connect(self.database)
        self.db.executescript(PUBLIC_SCHEMA)
        self.db.executescript(ENRICHMENT_SCHEMA)
        self.record = {
            "course_reference": {"subjects": ["COMPSCI"], "course_number": 300},
            "course_title": "Programming II",
            "description": "Classes and objects.",
            "prerequisites": {
                "prerequisites_text": "COMP SCI 200",
                "abstract_syntax_tree": "old parser",
            },
            "term_data": {"1262": {"grade_data": {"a": 1}}},
        }
        for run, when in [
            ("old", "2025-09-01T00:00:00+00:00"),
            ("new", "2026-09-01T00:00:00+00:00"),
        ]:
            self.db.execute(
                "INSERT INTO runs VALUES(?,?,?,?,?)",
                (run, "1272", when, "scrape", None),
            )
            record = json.loads(canonical(self.record))
            if run == "new":
                record["term_data"] = {}
                record["prerequisites"]["abstract_syntax_tree"] = "new parser"
            write_course(self.db, run, "COMPSCI 300", record)
            self.db.execute(
                "INSERT INTO terms VALUES(?,?,?)", (run, "1262", "Fall 2025")
            )
            self.db.execute(
                "INSERT INTO grades VALUES(?,?,?,?)",
                (
                    run,
                    "COMPSCI 300",
                    "1262",
                    canonical(
                        {
                            "a": 1 if run == "old" else 2,
                            "total": 2,
                            "instructors": ["Jane Example"],
                        }
                    ),
                ),
            )
        self.db.execute(
            'CREATE VIEW current_courses AS SELECT * FROM courses WHERE run_id="new"'
        )
        self.db.execute(
            "INSERT INTO offerings VALUES(?,?,?,?,?,?,?,?)",
            (
                "new",
                "offering-1",
                "1262",
                "COMPSCI 300",
                "123",
                "266",
                "{}",
                canonical(
                    {
                        "minimumCredits": 3,
                        "maximumCredits": 4,
                        "title": "Programming II",
                    }
                ),
            ),
        )
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def add_job(
        self, job, selected, status="valid", title="Object oriented programming"
    ):
        graph = {
            "status": "parsed",
            "root": "exclude",
            "nodes": [
                {"id": "exclude", "kind": "not", "children": ["course"]},
                {
                    "id": "course",
                    "kind": "course",
                    "course": {"subjects": ["COMPSCI"], "course_number": 367},
                },
            ],
        }
        output = {
            "task_version": 4,
            "sections": {
                "search_profile": {
                    "status": status,
                    "value": {
                        "summary": {"text": title},
                        "topics": [{"text": "Objects"}],
                        "skills_taught": [],
                        "search_phrases": ["java programming"],
                    },
                },
                "requirements": {"status": status, "value": graph},
                "student_experience": {
                    "status": "insufficient_evidence",
                    "value": {"themes": []},
                },
            },
        }
        self.db.execute(
            "INSERT INTO enrichment_jobs VALUES(?,?,?,?,?,?,?)",
            (job, "new", "unified", "{}", 1, 1, "2026-09-01T00:00:00+00:00"),
        )
        self.db.execute("INSERT INTO release_enrichments VALUES(?,?)", (job, selected))
        self.db.execute(
            "INSERT INTO enrichment_outputs VALUES(?,?,?,?,?)",
            (job, "qwen/model", "a" * 40, canonical(output), "{}"),
        )
        self.db.execute(
            "INSERT INTO course_enrichment_runs VALUES(?,?,?,?)",
            (job, "new", "COMPSCI 300", job),
        )
        self.db.commit()

    def export(self):
        output = self.root / "export"
        counts = write_public(self.database, output, "release-test", "new")
        return output, counts

    def test_catalog_history_ignores_term_activity_and_parser_versions(self):
        output, counts = self.export()
        self.assertEqual(counts["catalog_versions"], 1)
        history = pq.read_table(output / "public/courses_history.parquet").to_pylist()
        self.assertEqual(len(history), 2)
        self.assertNotEqual(
            history[0]["record_version_id"], history[1]["record_version_id"]
        )
        self.assertEqual(
            history[0]["catalog_version_id"], history[1]["catalog_version_id"]
        )
        modified = json.loads(canonical(self.record))
        modified["description"] = "Now teaches Java."
        self.assertNotEqual(
            catalog_record("COMPSCI 300", modified)["catalog_version_id"],
            history[0]["catalog_version_id"],
        )
        modified = json.loads(canonical(self.record))
        modified["prerequisites"]["prerequisites_text"] = "COMP SCI 200 or 220"
        self.assertNotEqual(
            catalog_record("COMPSCI 300", modified)["catalog_version_id"],
            history[0]["catalog_version_id"],
        )

    def test_typed_grades_deduplicate_snapshots_and_keep_missing_counts_null(self):
        output, counts = self.export()
        self.assertEqual(counts["grades_latest"], 1)
        grades = pq.read_table(output / "public/grades_latest.parquet")
        self.assertTrue(pa.types.is_integer(grades.schema.field("a").type))
        self.assertTrue(pa.types.is_list(grades.schema.field("instructors").type))
        self.assertTrue(pa.types.is_timestamp(grades.schema.field("observed_at").type))
        row = grades.to_pylist()[0]
        self.assertEqual(
            (row["run_id"], row["a"], row["total"], row["b"]), ("new", 2, 2, None)
        )
        course = pq.read_table(output / "public/courses_current.parquet").to_pylist()[0]
        self.assertEqual((course["credits_min"], course["credits_max"]), (3, 4))
        self.assertEqual(course["credit_offering_ids"], ["offering-1"])
        self.assertEqual(course["llm_search_status"], "not_generated")

    def test_only_selected_valid_sections_enter_search_and_requirement_graph(self):
        self.add_job("1-selected", 1)
        self.add_job("2-unselected", 0, title="Ignore this experiment")
        output, _ = self.export()
        course = pq.read_table(output / "public/courses_current.parquet").to_pylist()[0]
        self.assertEqual(course["llm_model_revision"], "a" * 40)
        self.assertEqual(course["llm_summary"], "Object oriented programming")
        self.assertIsNone(course["llm_experience_json"])
        index = json.loads((output / "serving/search.json").read_text())
        self.assertEqual(search_ids(index, "JAVA programming"), ["COMPSCI 300"])
        self.assertEqual(search_ids(index, "COMPSCI300"), ["COMPSCI 300"])
        self.assertEqual(search_ids(index, "experiment"), [])
        graph = json.loads((output / "serving/requirements.json").read_text())
        self.assertEqual(
            graph["courses"]["COMPSCI 300"]["ast"]["nodes"][0]["kind"], "not"
        )
        self.assertEqual(graph["release_id"], index["release_id"])
        shard = hashlib.sha256(b"COMPSCI 300").hexdigest()[:2]
        detail = json.loads((output / f"serving/courses/{shard}.json").read_text())
        self.assertEqual(detail["courses"]["COMPSCI 300"]["grades"][0]["a"], 2)
        self.assertEqual(detail["release_id"], "release-test")

    def test_newer_selected_invalid_output_does_not_fall_back_to_stale_valid_output(
        self,
    ):
        self.add_job("1-selected", 1)
        self.add_job("2-selected", 1, status="invalid", title="Rejected unicorn")
        output, _ = self.export()
        row = pq.read_table(output / "public/courses_current.parquet").to_pylist()[0]
        self.assertEqual(row["llm_search_status"], "invalid")
        self.assertIsNone(row["llm_summary"])
        self.assertIsNone(row["llm_requirements_ast_json"])
        index = json.loads((output / "serving/search.json").read_text())
        self.assertEqual(search_ids(index, "unicorn"), [])
        self.assertEqual(search_ids(index, "java"), [])
        self.assertEqual(search_ids(index, "classes"), ["COMPSCI 300"])

    def test_slim_release_is_verified_repeatable_and_references_archive(self):
        from uw_coursemap.release import checksum, verify_release
        import shutil

        archive = self.root / "releases" / "archive-test"
        archive.mkdir(parents=True)
        self.db.commit()
        shutil.copyfile(self.database, archive / "coursemap.sqlite")
        (archive / "manifest.json").write_text(
            canonical(
                {
                    "run_id": "archive-test",
                    "source_run": "new",
                    "input_hash": "source-hash",
                    "schema_version": 4,
                    "files": {
                        "coursemap.sqlite": {
                            "sha256": checksum(archive / "coursemap.sqlite"),
                            "bytes": (archive / "coursemap.sqlite").stat().st_size,
                        }
                    },
                }
            )
        )
        target = export_public(self.root, "archive-test")
        manifest = verify_release(target)
        self.assertEqual(manifest["archive_release"], "archive-test")
        self.assertEqual(
            manifest["archive_manifest_sha256"], checksum(archive / "manifest.json")
        )
        self.assertEqual(manifest["public_tables"]["courses_current"], 1)
        self.assertFalse((target / "coursemap.sqlite").exists())
        self.assertEqual(export_public(self.root, "archive-test"), target)
        with self.assertRaises(ValueError):
            export_public(self.root, "../archive-test")
        (target / "serving/search.json").write_text("corrupted")
        with self.assertRaisesRegex(ValueError, "checksum"):
            export_public(self.root, "archive-test")

    def test_trace_export_preserves_thinking_tools_retries_and_unselected_outputs(self):
        self.add_job("1-selected", 1)
        self.add_job("2-experiment", 0, status="invalid")
        value = json.loads(
            self.db.execute(
                "SELECT output_json FROM enrichment_outputs WHERE output_id='2-experiment'"
            ).fetchone()[0]
        )
        value["provenance"] = {
            "conversation": [
                {
                    "kind": "response",
                    "parts": [
                        {"part_kind": "thinking", "content": "Recorded Qwen reasoning"},
                        {
                            "part_kind": "tool-call",
                            "tool_name": "get_course",
                            "args": {"course_id": "COMPSCI 200"},
                        },
                    ],
                }
            ],
            "recovery_events": [
                {
                    "conversation": [
                        {
                            "kind": "request",
                            "parts": [
                                {
                                    "part_kind": "retry-prompt",
                                    "content": "Missing exclusion",
                                }
                            ],
                        }
                    ]
                }
            ],
            "worker_version": 17,
        }
        self.db.execute(
            "UPDATE enrichment_outputs SET output_json=?,usage_json=? WHERE output_id='2-experiment'",
            (canonical(value), '{"completion_tokens":123}'),
        )
        self.db.commit()
        output, counts = self.export()
        rows = pq.read_table(output / "public/llm_traces.parquet").to_pylist()
        self.assertEqual(counts["llm_traces"], 2)
        self.assertFalse(rows[0]["has_conversation"])
        self.assertFalse(rows[1]["selected_for_release"])
        self.assertTrue(rows[1]["has_conversation"])
        self.assertEqual(json.loads(rows[1]["output_json"]), value)
        self.assertEqual(rows[1]["model_revision"], "a" * 40)
        self.assertEqual(json.loads(rows[1]["usage_json"])["completion_tokens"], 123)
        self.assertNotIn(
            "Recorded Qwen reasoning", (output / "serving/search.json").read_text()
        )

    def test_large_trace_rows_are_byte_batched_without_losing_content(self):
        path = self.root / "bounded.parquet"
        schema = pa.schema([("output_json", pa.string())])
        rows = [{"output_json": "é" * n} for n in [20, 20, 60, 10]]
        self.assertEqual(write_rows(path, schema, iter(rows), max_text_bytes=100), 4)
        self.assertEqual(pq.read_metadata(path).num_row_groups, 3)
        self.assertEqual(pq.read_table(path).to_pylist(), rows)

    def test_selected_projection_does_not_retain_raw_traces(self):
        self.add_job("selected", 1)
        self.db.row_factory = sqlite3.Row
        selected = selected_enrichments(self.db)
        self.assertTrue(selected)
        for value in selected.values():
            self.assertNotIn("output_json", value)
            self.assertIn("llm_search_status", value)
            self.assertEqual(value["llm_job_id"], "selected")

    def test_archive_export_byte_batches_large_artifacts_losslessly(self):
        database = self.root / "large-archive.sqlite"
        payloads = ["é" * (5 * 1024 * 1024)] * 2 + ["x" * (18 * 1024 * 1024), None]
        with sqlite3.connect(database) as db:
            db.execute("CREATE TABLE artifacts(id INTEGER, payload TEXT)")
            db.executemany("INSERT INTO artifacts VALUES(?,?)", enumerate(payloads))
        directory = self.root / "large-archive-tables"
        self.assertEqual(write_parquet(database, directory), {"artifacts": 4})
        path = directory / "artifacts.parquet"
        self.assertEqual(pq.read_metadata(path).num_row_groups, 4)
        self.assertEqual(
            pq.read_table(path).to_pylist(),
            [{"id": i, "payload": value} for i, value in enumerate(payloads)],
        )

    def test_empty_tables_keep_schema_and_card_has_one_default(self):
        self.db.execute("DELETE FROM grades")
        self.db.execute("DELETE FROM offerings")
        self.db.commit()
        output, counts = self.export()
        self.assertEqual(
            pq.read_table(output / "public/grades_latest.parquet").schema,
            SCHEMAS["grades_latest"],
        )
        current = pq.read_table(output / "public/courses_current.parquet").to_pylist()[
            0
        ]
        self.assertIsNone(current["credits_min"])
        card = dataset_card("new", counts, {"grades": 2})
        self.assertEqual(card.count("default: true"), 1)
        self.assertIn("config_name: archive_grades", card)
        self.assertIn("latest observed distribution", card)
