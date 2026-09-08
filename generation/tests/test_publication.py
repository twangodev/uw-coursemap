import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from uw_coursemap.publication import publish_parquet
from uw_coursemap.release import checksum


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        directory = self.root / "releases/release-test"
        local = {
            "public/courses_current.parquet": b"public",
            "tables/courses.parquet": b"archive",
            "public/schema.json": b'{"version":4}',
            "coursemap.sqlite": b"private local archive",
            "serving/search.json": b"local serving",
        }
        for name, value in local.items():
            path = directory / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
        (directory / "manifest.json").write_text("{}")
        self.manifest = {
            "source_run": "source",
            "input_hash": "hash",
            "public_tables": {"courses_current": 1},
            "tables": {"courses": 1},
            "history": ["source"],
            "files": {
                n: {"bytes": len(v), "sha256": checksum(directory / n)}
                for n, v in local.items()
            },
        }
        self.store = SimpleNamespace(
            root=self.root,
            run=lambda run: {
                "run_id": run,
                "status": "complete",
                "started_at": "2026-01-01T00:00:00+00:00",
                "completed_at": "2026-01-01T01:00:00+00:00",
            },
            input_hash=lambda run: "hash",
        )
        self.files = {"sync.json": b"old sync"}
        self.head = "old"
        self.commits = []
        self.api = SimpleNamespace(
            create_repo=lambda **kw: None,
            repo_info=lambda **kw: SimpleNamespace(sha=self.head),
            list_repo_files=lambda **kw: list(self.files),
            create_commit=self.commit,
            get_paths_info=self.infos,
        )

    def commit(self, **kwargs):
        self.assertEqual(kwargs["parent_commit"], self.head)
        self.commits.append(kwargs)
        updated = {
            op.path_in_repo: op.path_or_fileobj
            if isinstance(op.path_or_fileobj, bytes)
            else Path(op.path_or_fileobj).read_bytes()
            for op in kwargs["operations"]
        }
        self.files.update(updated)
        self.head = "new"
        return SimpleNamespace(oid=self.head)

    def infos(self, **kwargs):
        return [
            SimpleNamespace(
                path=n,
                size=len(self.files[n]),
                lfs=SimpleNamespace(sha256=hashlib.sha256(self.files[n]).hexdigest()),
            )
            for n in kwargs["paths"]
        ]

    def publish(self):
        with (
            patch(
                "uw_coursemap.publication.verify_release", return_value=self.manifest
            ),
            patch("huggingface_hub.DatasetCard.validate"),
        ):
            return publish_parquet(
                self.store, "release-test", "owner/dataset", api=self.api
            )

    def test_atomic_data_card_and_sync_exclude_sqlite_and_serving(self):
        result = self.publish()
        self.assertEqual(result["status"], "complete")
        self.assertEqual(len(self.commits), 1)
        self.assertEqual(
            set(self.files),
            {
                "public/courses_current.parquet",
                "tables/courses.parquet",
                "public/schema.json",
                "README.md",
                "manifest.json",
                "sync.json",
            },
        )
        sync = json.loads(self.files["sync.json"])
        self.assertNotIn("data_revision", sync)
        self.assertEqual(
            sync["manifest_sha256"],
            hashlib.sha256(self.files["manifest.json"]).hexdigest(),
        )
        self.assertIn("archive_courses", self.files["README.md"].decode())

    def test_failed_commit_preserves_existing_sync(self):
        def failure(**kwargs):
            raise RuntimeError("upload failed")

        self.api.create_commit = failure
        with self.assertRaisesRegex(RuntimeError, "upload failed"):
            self.publish()
        self.assertEqual(self.files, {"sync.json": b"old sync"})
        self.assertEqual(self.head, "old")

    def test_missing_remote_hash_cannot_be_marked_complete(self):
        self.api.get_paths_info = lambda **kwargs: []
        with self.assertRaisesRegex(ValueError, "every published file"):
            self.publish()
        checkpoint = next((self.root / "publications").glob("*.json"))
        self.assertEqual(json.loads(checkpoint.read_text())["status"], "verifying")
