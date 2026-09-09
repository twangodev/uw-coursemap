import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from uwcourses_site.deployment import (
    Release,
    deploy,
    select_slot,
    verify_database,
    worker_state,
)


class DeploymentTests(unittest.TestCase):
    release = Release("a" * 40, "b" * 64, 10)

    def test_first_deployment_is_explicit(self):
        with self.assertRaises(ValueError):
            select_slot(None, self.release, False)
        self.assertEqual(select_slot(None, self.release, True).binding, "DB_A")

    def test_only_inactive_slot_is_imported(self):
        for active, target in (("a", "b"), ("b", "a")):
            plan = select_slot({"DATA_SLOT": active}, self.release, False)
            self.assertEqual(plan.slot, target)
            self.assertTrue(plan.import_required)
        with self.assertRaises(ValueError):
            select_slot({"DATA_SLOT": "unknown"}, self.release, True)

    def test_same_projection_reuses_active_database(self):
        plan = select_slot(
            {"DATA_SLOT": "b", "DATA_PROJECTION": self.release.projection},
            self.release,
            False,
        )
        self.assertEqual(plan.slot, "b")
        self.assertFalse(plan.import_required)

    def report(self, **changes):
        status = {
            "revision": self.release.revision,
            "projection_id": self.release.projection,
        }
        return json.dumps(
            [
                {
                    "success": True,
                    "results": [
                        {
                            "ready": "true",
                            "courses": 10,
                            "status": json.dumps(status),
                            **changes,
                        }
                    ],
                }
            ]
        )

    def test_staged_database_must_match(self):
        verify_database(self.report(), self.release)
        for changes in ({"ready": "false"}, {"courses": 9}, {"status": "{}"}):
            with self.assertRaises(ValueError):
                verify_database(self.report(**changes), self.release)

    def run_deploy(self, failure=None, changed=False, reuse=False):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sql").mkdir()
            for name in ("0001.sql", "0002.sql"):
                (root / "sql" / name).write_text("SELECT 1;")
            (root / "status.json").write_text(
                json.dumps(
                    {
                        "limited": False,
                        "revision": self.release.revision,
                        "projection_id": self.release.projection,
                        "courses": 10,
                    }
                )
            )
            config = root / "wrangler.json"
            config.write_text(
                json.dumps(
                    {
                        "name": "uw-coursemap",
                        "d1_databases": [
                            {"binding": "DB_A", "database_id": "a"},
                            {"binding": "DB_B", "database_id": "b"},
                        ],
                    }
                )
            )
            initial = {
                "DATA_SLOT": "a",
                "DATA_PROJECTION": self.release.projection if reuse else "old",
            }
            states = [initial, {"DATA_SLOT": "b"} if changed else initial]
            calls = []

            def command(config, *args, **kwargs):
                calls.append(args)
                if failure == "import" and "--file" in args:
                    raise subprocess.CalledProcessError(1, ["wrangler"])
                return self.report(courses=0) if failure == "verify" else self.report()

            with (
                patch.dict(
                    "os.environ",
                    {"CLOUDFLARE_ACCOUNT_ID": "a" * 32, "CLOUDFLARE_API_TOKEN": "test"},
                ),
                patch("uwcourses_site.deployment.worker_state", side_effect=states),
                patch("uwcourses_site.deployment.wrangler", side_effect=command),
                patch("uwcourses_site.deployment.subprocess.run") as run,
            ):
                run.return_value.stdout = "c" * 40
                if failure or changed:
                    with self.assertRaises(
                        (ValueError, RuntimeError, subprocess.CalledProcessError)
                    ):
                        deploy(config, root)
                    self.assertFalse(any(call[0] == "deploy" for call in calls))
                else:
                    deploy(config, root)
                    self.assertEqual(calls[-1][0], "deploy")
                    imports = [call for call in calls if "--file" in call]
                    self.assertEqual(len(imports), 0 if reuse else 2)
                    if imports:
                        self.assertTrue(all(call[2] == "DB_B" for call in imports))
                        self.assertTrue(imports[0][-1].endswith("0001.sql"))

    def test_import_verify_and_publish_order(self):
        self.run_deploy()

    def test_reuse_still_verifies_before_publish(self):
        self.run_deploy(reuse=True)

    def test_import_failure_stops_publish(self):
        self.run_deploy(failure="import")

    def test_verification_failure_stops_publish(self):
        self.run_deploy(failure="verify")

    def test_concurrent_change_stops_publish(self):
        self.run_deploy(changed=True)

    def test_incomplete_release_rejected(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "status.json"
            path.write_text(json.dumps({"limited": True}))
            with self.assertRaises(ValueError):
                Release.read(path)

    @patch("uwcourses_site.deployment.requests.get")
    def test_only_404_means_missing_worker(self, get):
        get.return_value.status_code = 404
        self.assertIsNone(worker_state("account", "token", "worker"))
        get.return_value.status_code = 403
        get.return_value.raise_for_status.side_effect = RuntimeError("Forbidden")
        with self.assertRaises(RuntimeError):
            worker_state("account", "token", "worker")
