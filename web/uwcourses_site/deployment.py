"""Publish a verified website release with native Wrangler commands.

The inactive D1 slot is imported and verified before changing the live Worker.
No shell is involved; a failed import/verification never proceeds to deployment.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any

import requests


@dataclass(frozen=True)
class Release:
    revision: str
    projection: str
    courses: int

    @classmethod
    def read(cls, path: Path) -> "Release":
        data = json.loads(path.read_text())
        if (
            data.get("limited") is not False
            or not re.fullmatch(r"[a-f0-9]{40}", data.get("revision", ""))
            or not re.fullmatch(r"[a-f0-9]{64}", data.get("projection_id", ""))
            or not isinstance(data.get("courses"), int)
            or data["courses"] < 1
        ):
            raise ValueError("Deployment requires a complete, pinned dataset release")
        return cls(data["revision"], data["projection_id"], data["courses"])


@dataclass(frozen=True)
class Plan:
    slot: str
    import_required: bool

    @property
    def binding(self) -> str:
        return "DB_" + self.slot.upper()


def select_slot(state: dict[str, str] | None, release: Release, first: bool) -> Plan:
    if state is None:
        if not first:
            raise ValueError(
                "Worker does not exist; enable first deployment explicitly"
            )
        return Plan("a", True)
    active = state.get("DATA_SLOT")
    if active not in ("a", "b"):
        raise ValueError("Cannot determine the active D1 slot; refusing to import")
    if state.get("DATA_PROJECTION") == release.projection:
        return Plan(active, False)
    return Plan("b" if active == "a" else "a", True)


def worker_state(account: str, token: str, worker: str) -> dict[str, str] | None:
    response = requests.get(
        f"https://api.cloudflare.com/client/v4/accounts/{account}/workers/scripts/{worker}/settings",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    data = response.json()
    if data.get("success") is not True:
        raise RuntimeError("Cloudflare could not read the current Worker settings")
    names = {"DATA_SLOT", "DATA_PROJECTION", "SITE_COMMIT"}
    return {
        binding["name"]: binding["text"]
        for binding in data["result"]["bindings"]
        if binding.get("name") in names and "text" in binding
    }


def wrangler(config: Path, *args: str, capture: bool = False) -> str:
    result = subprocess.run(
        ["bun", "x", "--no-install", "wrangler", "--config", str(config), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
    )
    return result.stdout or ""


def verify_database(output: str, release: Release) -> Any:
    results = json.loads(output)
    if not results or results[0].get("success") is False:
        raise ValueError("Staged D1 verification failed")
    row = results[0]["results"][0]
    status = json.loads(row["status"])
    if (
        row["ready"] != "true"
        or row["courses"] != release.courses
        or status.get("projection_id") != release.projection
        or status.get("revision") != release.revision
    ):
        raise ValueError("Staged database does not match the built release")
    return results


def deploy(config: Path, site: Path, first: bool = False) -> None:
    release = Release.read(site / "status.json")
    settings = json.loads(config.read_text())
    worker = settings["name"]
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", worker):
        raise ValueError("Invalid Worker name")
    databases = {row["binding"]: row["database_id"] for row in settings["d1_databases"]}
    if (
        not {"DB_A", "DB_B"} <= databases.keys()
        or databases["DB_A"] == databases["DB_B"]
    ):
        raise ValueError("Configure distinct DB_A and DB_B databases")
    account = os.environ["CLOUDFLARE_ACCOUNT_ID"]
    token = os.environ["CLOUDFLARE_API_TOKEN"]
    if not re.fullmatch(r"[a-fA-F0-9]{32}", account) or not token:
        raise ValueError("Set valid Cloudflare account credentials")
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    state = worker_state(account, token, worker)
    plan = select_slot(state, release, first)
    print(
        f"Release {release.revision}: slot {plan.slot.upper()}, import={plan.import_required}",
        flush=True,
    )
    if plan.import_required:
        parts = sorted((site / "sql").glob("*.sql"))
        if not parts:
            raise ValueError("No dataset SQL import files found")
        for part in parts:
            wrangler(
                config, "d1", "execute", plan.binding, "--remote", "--file", str(part)
            )
    output = wrangler(
        config,
        "d1",
        "execute",
        plan.binding,
        "--remote",
        "--json",
        "--command",
        "SELECT (SELECT value FROM metadata WHERE key='ready') ready, "
        "(SELECT value FROM metadata WHERE key='status') status, "
        "(SELECT count(*) FROM courses) courses",
        capture=True,
    )
    report = verify_database(output, release)
    (site / "d1-check.json").write_text(json.dumps(report, indent=2) + "\n")
    if worker_state(account, token, worker) != state:
        raise RuntimeError("Worker changed during preparation; refusing to replace it")
    wrangler(
        config,
        "deploy",
        "--var",
        f"DATA_SLOT:{plan.slot}",
        "--var",
        f"SITE_COMMIT:{commit}",
        "--var",
        f"DATA_PROJECTION:{release.projection}",
        "--var",
        f"DEPLOYED_AT:{datetime.now(timezone.utc).isoformat()}",
    )
