"""Resumable enrichment jobs with bounded HTTP workers and one result writer."""

from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
import time

import jsonschema
import requests

from .models import canonical, digest
from .profiles import load_profile
from .store import Store, now


WORKER_VERSION = 4


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
    headers = {}
    if os.environ.get("COURSEMAP_INFERENCE_API_KEY"):
        headers["Authorization"] = "Bearer " + os.environ["COURSEMAP_INFERENCE_API_KEY"]
    messages = [
        {
            "role": "system",
            "content": task["prompt"]
            + "\nOutput JSON schema:\n"
            + json.dumps(task["schema"], ensure_ascii=False),
        },
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]
    for attempt in range(3):
        content = None
        try:
            response = requests.post(
                profile["base_url"].rstrip("/") + "/chat/completions",
                headers=headers,
                json={
                    "model": f"{profile['model']}@{profile['revision']}",
                    "messages": list(messages),
                    "max_tokens": profile["max_output_tokens"],
                    "temperature": profile["temperature"],
                    "chat_template_kwargs": {"enable_thinking": profile["thinking"]},
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": task["name"],
                            "strict": True,
                            "schema": generation_schema(task["schema"]),
                        },
                    },
                },
                timeout=(10, 180),
            )
            response.raise_for_status()
            data = response.json()
            if data.get("model") != f"{profile['model']}@{profile['revision']}":
                raise ValueError("Server returned a different model identity")
            choice = data["choices"][0]
            if choice["finish_reason"] != "stop":
                raise ValueError("Model output was truncated or incomplete")
            content = choice["message"]["content"]
            value = json.loads(content)
            jsonschema.Draft202012Validator(task["schema"]).validate(value)
            for field in task.get("evidence_fields", []):
                for item in value[field]:
                    if item["evidence"] not in (payload.get("description") or ""):
                        raise ValueError(
                            "Evidence quote is absent from the source description"
                        )
            if task.get("validator") == "requirements_graph_v1":
                from .requirements import restore_quotes, validate_graph

                restore_quotes(value, payload)
                validate_graph(value, payload)
            return value, data.get("usage", {})
        except requests.HTTPError as exc:
            if response.status_code not in {429, 500, 502, 503, 504} or attempt == 2:
                raise ValueError(f"Inference HTTP {response.status_code}") from exc
        except (
            requests.RequestException,
            ValueError,
            KeyError,
            IndexError,
            jsonschema.ValidationError,
        ) as exc:
            if attempt == 2:
                raise
            if content is not None:
                # Keep one correction turn so retries fit the original context.
                reason = (
                    exc.message
                    if isinstance(exc, jsonschema.ValidationError)
                    else str(exc)
                )
                messages[2:] = [
                    {"role": "assistant", "content": content},
                    {
                        "role": "user",
                        "content": "Validation failed: "
                        + reason[:600]
                        + ". Return a corrected complete JSON object using only the original source. Do not invent missing evidence.",
                    },
                ]
        time.sleep(2**attempt)


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

    def create(self, source_run, profiles, profile_name, task_path, limit=100):
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
        fields = task.get(
            "input_fields",
            ["course_reference", "course_title", "description", "prerequisites"],
        )
        source = Store(self.root, readonly=True)
        try:
            from .lifecycle import require_snapshot

            require_snapshot(source, source_run)
            courses = source.records(source_run, "courses")
            if not courses:
                raise ValueError("Snapshot has no courses")
            # Stable hash sampling avoids an alphabetically biased pilot.
            selected = sorted(courses, key=lambda key: digest(key))
            if limit:
                selected = selected[:limit]
            spec = {
                "task": task,
                "profile": profile.model_dump(),
                "source_hash": source.input_hash(source_run),
                "total_courses": len(courses),
                "selected_courses": len(selected),
                "worker_version": WORKER_VERSION,
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
                    if isinstance(fields, dict):
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
                        }
                    )
                    self.db.execute(
                        "INSERT OR IGNORE INTO results(job_id,course_id,cache_key,input_json,status) VALUES(?,?,?,?,'pending')",
                        (job, key, cache_key, canonical(payload)),
                    )
            return job
        finally:
            source.close()

    def run(self, job, worker=generate):
        with file_lock(self.root / "jobs" / f"{job}.lock"):
            status = self.status(job)
            if status["status"] == "complete":
                return status
            spec = json.loads(status["spec_json"])
            if spec["worker_version"] != WORKER_VERSION:
                raise ValueError(
                    "Enrichment worker changed; create a new job with current provenance"
                )
            if worker is generate:
                check_server(spec["profile"])
            source = Store(self.root, readonly=True)
            try:
                if source.input_hash(status["source_run"]) != spec["source_hash"]:
                    raise ValueError("Source snapshot changed")
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
                    if cached:
                        with self.db:
                            self.db.execute(
                                "UPDATE results SET status='complete',output_json=?,usage_json=?,error=NULL WHERE job_id=? AND course_id=?",
                                (*tuple(cached), job, row["course_id"]),
                            )
                        continue
                    pending[
                        pool.submit(
                            worker,
                            spec["profile"],
                            spec["task"],
                            json.loads(row["input_json"]),
                        )
                    ] = row
                    return

            with ThreadPoolExecutor(max_workers=spec["profile"]["concurrency"]) as pool:
                for _ in range(spec["profile"]["concurrency"]):
                    submit_next(pool)
                while pending:
                    done, _ = wait(pending, return_when=FIRST_COMPLETED)
                    for future in done:
                        row = pending.pop(future)
                        try:
                            value, usage = future.result()
                            encoded, tokens = canonical(value), canonical(usage)
                            with self.db:
                                self.db.execute(
                                    "INSERT OR IGNORE INTO output_cache VALUES(?,?,?)",
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
    def append_release(root, path, source_run, ids):
        with sqlite3.connect(path) as output:
            output.execute("PRAGMA foreign_keys=ON")
            output.executescript("""
            CREATE TABLE enrichment_jobs(job_id TEXT PRIMARY KEY,run_id TEXT REFERENCES runs,task TEXT,spec_json TEXT,selected_courses INTEGER,total_courses INTEGER);
            CREATE TABLE course_enrichments(job_id TEXT REFERENCES enrichment_jobs,run_id TEXT,course_id TEXT,output_json TEXT,usage_json TEXT,PRIMARY KEY(job_id,course_id),FOREIGN KEY(run_id,course_id) REFERENCES courses);
            """)
            if not ids:
                return
            uri = (Path(root) / "processing.sqlite").resolve().as_uri() + "?mode=ro"
            jobs = sqlite3.connect(uri, uri=True)
            jobs.row_factory = sqlite3.Row
            try:
                for job in sorted(set(ids)):
                    row = jobs.execute(
                        "SELECT * FROM jobs WHERE job_id=?", (job,)
                    ).fetchone()
                    if (
                        not row
                        or row["status"] != "complete"
                        or row["source_run"] != source_run
                    ):
                        raise ValueError(
                            "Release requires completed enrichment jobs from the selected snapshot"
                        )
                    spec = json.loads(row["spec_json"])
                    count = jobs.execute(
                        "SELECT count(*) FROM results WHERE job_id=? AND status='complete'",
                        (job,),
                    ).fetchone()[0]
                    if count != spec["selected_courses"]:
                        raise ValueError(
                            "Enrichment coverage does not match its completed job"
                        )
                    public_spec = json.loads(row["spec_json"])
                    public_spec["profile"].pop("base_url", None)
                    output.execute(
                        "INSERT INTO enrichment_jobs VALUES(?,?,?,?,?,?)",
                        (
                            job,
                            source_run,
                            spec["task"]["name"],
                            canonical(public_spec),
                            spec["selected_courses"],
                            spec["total_courses"],
                        ),
                    )
                    output.executemany(
                        "INSERT INTO course_enrichments VALUES(?,?,?,?,?)",
                        (
                            (
                                job,
                                source_run,
                                r["course_id"],
                                r["output_json"],
                                r["usage_json"],
                            )
                            for r in jobs.execute(
                                "SELECT * FROM results WHERE job_id=? AND status='complete' ORDER BY course_id",
                                (job,),
                            )
                        ),
                    )
            finally:
                jobs.close()
            if output.execute("PRAGMA foreign_key_check").fetchall():
                raise ValueError("Enrichment references missing courses")
