"""Resumable enrichment jobs with bounded HTTP workers and one result writer."""

from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3

import jsonschema
import requests

from .models import canonical, digest
from .profiles import load_profile
from .store import Store, now


WORKER_VERSION = 15


def generation_schema(schema):
    """Keep full post-validation while adapting unsupported grammar keywords."""
    import copy

    result = copy.deepcopy(schema)

    def visit(node):
        if not isinstance(node, dict):
            return
        node.pop("uniqueItems", None)
        for key in (
            "properties",
            "$defs",
            "definitions",
            "patternProperties",
            "dependentSchemas",
        ):
            for child in node.get(key, {}).values():
                visit(child)
        for key in (
            "items",
            "additionalProperties",
            "contains",
            "not",
            "if",
            "then",
            "else",
        ):
            visit(node.get(key))
        for key in ("allOf", "anyOf", "oneOf", "prefixItems"):
            for child in node.get(key, []):
                visit(child)

    visit(result)
    return result


@contextmanager
def file_lock(path):
    import fcntl

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("This operation already has an active worker") from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def check_server(profile):
    headers = {}
    if os.environ.get("COURSEMAP_INFERENCE_API_KEY"):
        headers["Authorization"] = "Bearer " + os.environ["COURSEMAP_INFERENCE_API_KEY"]
    try:
        response = requests.get(
            profile["base_url"].rstrip("/") + "/models",
            headers=headers,
            timeout=(10, 30),
        )
        response.raise_for_status()
        identity = f"{profile['model']}@{profile['revision']}"
        if identity not in {row["id"] for row in response.json()["data"]}:
            raise ValueError("Inference server is not serving the pinned model")
    except requests.RequestException as exc:
        raise RuntimeError(
            "Inference server unavailable; start the pinned model and resume this job"
        ) from exc


def generate(profile, task, payload):
    from .agents import generate_generic

    return generate_generic(profile, task, payload)


class Jobs:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / "processing.sqlite", timeout=30)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS jobs(job_id TEXT PRIMARY KEY, source_run TEXT NOT NULL, spec_json TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS results(job_id TEXT REFERENCES jobs, course_id TEXT, cache_key TEXT NOT NULL, input_json TEXT NOT NULL, status TEXT NOT NULL, output_json TEXT, usage_json TEXT, error TEXT, attempts INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(job_id,course_id));
        CREATE TABLE IF NOT EXISTS output_cache(cache_key TEXT PRIMARY KEY, output_json TEXT NOT NULL, usage_json TEXT NOT NULL);
        """)

    def close(self):
        self.db.close()

    def status(self, job):
        row = self.db.execute("SELECT * FROM jobs WHERE job_id=?", (job,)).fetchone()
        if row is None:
            raise ValueError("Unknown enrichment job")
        return {
            **dict(row),
            "counts": dict(
                self.db.execute(
                    "SELECT status,count(*) FROM results WHERE job_id=? GROUP BY status",
                    (job,),
                )
            ),
        }

    def create(
        self, source_run, profiles, profile_name, task_path, limit=100, course_ids=None
    ):
        if limit < 0:
            raise ValueError("limit must be nonnegative")
        profile = load_profile(profiles, profile_name)
        if profile.runner != "generate":
            raise ValueError("Enrichment requires a generation profile")
        task = json.loads(Path(task_path).read_text())
        if not task.get("name") or not task.get("prompt") or not task.get("version"):
            raise ValueError("Task must have a name, version, prompt, and JSON schema")
        jsonschema.Draft202012Validator.check_schema(task["schema"])
        if task.get("validator") not in {None, "requirements_graph_v1"}:
            raise ValueError("Unknown task validator")
        if task.get("workflow") not in {None, "unified_v1"}:
            raise ValueError("Unknown enrichment workflow")
        fields = task.get(
            "input_fields",
            ["course_reference", "course_title", "description", "prerequisites"],
        )
        source = Store(self.root, readonly=True)
        try:
            from .lifecycle import require_snapshot

            require_snapshot(source, source_run)
            courses = source.records(source_run, "courses")
            from .course_context import CourseContext

            context = (
                CourseContext(source, source_run)
                if task.get("workflow") == "unified_v1" or course_ids
                else None
            )
            if not courses:
                raise ValueError("Snapshot has no courses")
            # Stable hash sampling avoids an alphabetically biased pilot.
            selected = sorted(courses, key=lambda key: digest(key))
            if limit:
                selected = selected[:limit]
            if course_ids:
                selected = sorted(
                    {context.resolve(key) for key in course_ids},
                    key=lambda key: key or "",
                )
                if None in selected:
                    raise ValueError(
                        "Selected course is missing or ambiguous in the snapshot"
                    )
            from .agents import ORCHESTRATOR

            spec = {
                "task": task,
                "profile": profile.model_dump(),
                "source_hash": source.input_hash(source_run),
                "total_courses": len(courses),
                "selected_courses": len(selected),
                "worker_version": WORKER_VERSION,
                "orchestrator": ORCHESTRATOR,
            }
            job = (
                "enrich-"
                + digest(
                    {"source_run": source_run, "spec": spec, "selection": selected}
                )[:24]
            )
            with self.db:
                self.db.execute(
                    "INSERT OR IGNORE INTO jobs VALUES(?,?,?,'pending',?)",
                    (job, source_run, canonical(spec), now()),
                )
                for key in selected:
                    if task.get("workflow") == "unified_v1":
                        payload = context.get(key)
                    elif isinstance(fields, dict):
                        payload = {}
                        for field, path in fields.items():
                            value = courses[key]
                            for part in path.split("."):
                                value = (
                                    value.get(part) if isinstance(value, dict) else None
                                )
                            payload[field] = value
                    else:
                        payload = {field: courses[key].get(field) for field in fields}
                    cache_profile = profile.model_dump(
                        exclude={"base_url", "concurrency"}
                    )
                    cache_key = digest(
                        {
                            "input": payload,
                            "task": task,
                            "profile": cache_profile,
                            "worker_version": WORKER_VERSION,
                            "orchestrator": ORCHESTRATOR,
                        }
                    )
                    self.db.execute(
                        "INSERT OR IGNORE INTO results(job_id,course_id,cache_key,input_json,status) VALUES(?,?,?,?,'pending')",
                        (job, key, cache_key, canonical(payload)),
                    )
            return job
        finally:
            source.close()

    def run(self, job, worker=generate, concurrency=None):
        with file_lock(self.root / "jobs" / f"{job}.lock"):
            status = self.status(job)
            if status["status"] == "complete":
                return status
            spec = json.loads(status["spec_json"])
            concurrency = (
                concurrency
                if concurrency is not None
                else spec["profile"]["concurrency"]
            )
            if not 1 <= concurrency <= 512:
                raise ValueError("Concurrency must be between 1 and 512")
            if spec["worker_version"] != WORKER_VERSION:
                raise ValueError(
                    "Enrichment worker changed; create a new job with current provenance"
                )
            if worker is generate:
                check_server(spec["profile"])
            source = Store(self.root, readonly=True)
            context = None
            try:
                if source.input_hash(status["source_run"]) != spec["source_hash"]:
                    raise ValueError("Source snapshot changed")
                if spec["task"].get("workflow") == "unified_v1":
                    from .course_context import CourseContext

                    context = CourseContext(source, status["source_run"])
            finally:
                source.close()
            with self.db:
                self.db.execute(
                    "UPDATE jobs SET status='running' WHERE job_id=?", (job,)
                )
            rows = iter(
                self.db.execute(
                    "SELECT * FROM results WHERE job_id=? AND status!='complete' ORDER BY course_id",
                    (job,),
                ).fetchall()
            )
            pending = {}

            def submit_next(pool):
                for row in rows:
                    cached = self.db.execute(
                        "SELECT output_json,usage_json FROM output_cache WHERE cache_key=?",
                        (row["cache_key"],),
                    ).fetchone()
                    if cached and context is not None:
                        dependencies = (
                            json.loads(cached[0])
                            .get("provenance", {})
                            .get("dependencies", {})
                        )
                        if any(
                            context.fingerprint(key) != stamp
                            for key, stamp in dependencies.items()
                        ):
                            cached = None
                    if cached:
                        with self.db:
                            self.db.execute(
                                "UPDATE results SET status='complete',output_json=?,usage_json=?,error=NULL WHERE job_id=? AND course_id=?",
                                (*tuple(cached), job, row["course_id"]),
                            )
                        continue
                    args = [
                        spec["profile"],
                        spec["task"],
                        json.loads(row["input_json"]),
                    ]
                    selected_worker = worker
                    if context is not None and worker is generate:
                        from .agents import generate_unified

                        selected_worker = generate_unified
                        if spec["task"].get("repair_mode") == "conversation_v1":
                            from .agents import generate_repair

                            selected_worker = generate_repair
                        args.append(context)
                    pending[pool.submit(selected_worker, *args)] = row
                    return

            with ThreadPoolExecutor(max_workers=concurrency) as pool:
                for _ in range(concurrency):
                    submit_next(pool)
                while pending:
                    done, _ = wait(pending, return_when=FIRST_COMPLETED)
                    for future in done:
                        row = pending.pop(future)
                        try:
                            value, usage = future.result()
                            if context is not None:
                                value.setdefault("provenance", {})[
                                    "generated_from_snapshot"
                                ] = status["source_run"]
                            value.setdefault("provenance", {})["client_concurrency"] = (
                                concurrency
                            )
                            encoded, tokens = canonical(value), canonical(usage)
                            with self.db:
                                self.db.execute(
                                    "INSERT OR REPLACE INTO output_cache VALUES(?,?,?)",
                                    (row["cache_key"], encoded, tokens),
                                )
                                self.db.execute(
                                    "UPDATE results SET status='complete',output_json=?,usage_json=?,error=NULL,attempts=attempts+1 WHERE job_id=? AND course_id=?",
                                    (encoded, tokens, job, row["course_id"]),
                                )
                        except Exception as exc:
                            error = type(exc).__name__
                            if isinstance(
                                exc, (ValueError, jsonschema.ValidationError)
                            ):
                                reason = (
                                    exc.message
                                    if isinstance(exc, jsonschema.ValidationError)
                                    else str(exc)
                                )
                                error += ": " + reason[:600]
                            with self.db:
                                self.db.execute(
                                    "UPDATE results SET status='failed',error=?,attempts=attempts+1 WHERE job_id=? AND course_id=?",
                                    (error, job, row["course_id"]),
                                )
                        submit_next(pool)
            remaining = self.db.execute(
                "SELECT count(*) FROM results WHERE job_id=? AND status!='complete'",
                (job,),
            ).fetchone()[0]
            with self.db:
                self.db.execute(
                    "UPDATE jobs SET status=? WHERE job_id=?",
                    ("failed" if remaining else "complete", job),
                )
            if remaining:
                raise RuntimeError(
                    f"{remaining} enrichments failed; resume {job} to retry only failed rows"
                )
            return self.status(job)

    @staticmethod
    def append_release(root, path, source_run, ids, history=None):
        from .history import export_enrichments

        export_enrichments(root, path, source_run, ids, history)
