"""Content-addressed course versions and complete released enrichment history."""

import hashlib
import json
import sqlite3
from pathlib import Path

from .models import canonical, digest


def write_course(db, run, key, value):
    fields = (
        value["course_reference"]["course_number"],
        value["course_title"],
        value["description"],
        canonical(value["prerequisites"]),
        canonical(value),
    )
    version = digest(value)
    db.execute(
        "INSERT OR IGNORE INTO course_versions VALUES(?,?,?,?,?,?)", (version, *fields)
    )
    db.execute("INSERT INTO course_snapshots VALUES(?,?,?)", (run, key, version))


def job_stamp(db, row):
    spec = json.loads(row["spec_json"])
    hasher = hashlib.sha256()
    count = 0
    for result in db.execute(
        "SELECT course_id,status,output_json,usage_json FROM results WHERE job_id=? ORDER BY course_id",
        (row["job_id"],),
    ):
        if result["status"] != "complete" or result["output_json"] is None:
            raise ValueError("Enrichment coverage does not match its completed job")
        hasher.update(canonical(list(result)).encode())
        hasher.update(b"\n")
        count += 1
    if count != spec["selected_courses"]:
        raise ValueError("Enrichment coverage does not match its completed job")
    return {
        "job_id": row["job_id"],
        "source_run": row["source_run"],
        "spec_hash": digest(spec),
        "results_hash": hasher.hexdigest(),
    }


def select_enrichments(root, runs, selected, current_run, include_all=True):
    """Freeze completed jobs, including a content fingerprint for release identity."""
    selected, runs = set(selected), set(runs)
    path = Path(root) / "processing.sqlite"
    if not path.exists():
        if selected:
            raise ValueError("Release requires completed enrichment jobs")
        return []
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        db.execute("BEGIN")
        rows = list(db.execute("SELECT * FROM jobs ORDER BY job_id"))
        by_id = {row["job_id"]: row for row in rows}
        for key in selected:
            row = by_id.get(key)
            if not row or row["status"] != "complete" or row["source_run"] not in runs:
                raise ValueError(
                    "Release requires completed enrichment jobs from included snapshots"
                )
        return [
            {**job_stamp(db, row), "selected": row["job_id"] in selected}
            for row in rows
            if row["status"] == "complete"
            and row["source_run"] in runs
            and (include_all or row["job_id"] in selected)
        ]
    finally:
        db.close()


ENRICHMENT_SCHEMA = """
CREATE TABLE enrichment_jobs(job_id TEXT PRIMARY KEY,run_id TEXT REFERENCES runs,task TEXT,spec_json TEXT,selected_courses INTEGER,total_courses INTEGER,created_at TEXT);
CREATE TABLE release_enrichments(job_id TEXT PRIMARY KEY REFERENCES enrichment_jobs,is_selected INTEGER NOT NULL);
CREATE TABLE enrichment_outputs(output_id TEXT PRIMARY KEY,model TEXT,model_revision TEXT,output_json TEXT,usage_json TEXT);
CREATE TABLE course_enrichment_runs(job_id TEXT REFERENCES enrichment_jobs,run_id TEXT,course_id TEXT,output_id TEXT REFERENCES enrichment_outputs,PRIMARY KEY(job_id,course_id),FOREIGN KEY(run_id,course_id) REFERENCES course_snapshots);
CREATE TABLE enrichment_output_sections(output_id TEXT REFERENCES enrichment_outputs,section TEXT,status TEXT,value_json TEXT,candidate_json TEXT,error TEXT,PRIMARY KEY(output_id,section));
CREATE VIEW course_enrichments AS SELECT b.job_id,b.run_id,b.course_id,o.output_json,o.usage_json FROM course_enrichment_runs b JOIN enrichment_outputs o USING(output_id);
CREATE VIEW enrichment_sections AS SELECT b.job_id,b.course_id,s.section,s.status,o.model,o.model_revision,s.value_json,s.candidate_json,s.error FROM course_enrichment_runs b JOIN enrichment_outputs o USING(output_id) JOIN enrichment_output_sections s USING(output_id);
CREATE VIEW course_enrichment_history AS SELECT b.*,r.semester,r.observed_at,c.version_id,j.task,j.created_at,o.model,o.model_revision FROM course_enrichment_runs b JOIN runs r USING(run_id) JOIN course_snapshots c USING(run_id,course_id) JOIN enrichment_jobs j USING(job_id) JOIN enrichment_outputs o USING(output_id);
CREATE VIEW current_course_enrichments AS SELECT e.* FROM course_enrichments e JOIN current_courses c USING(run_id,course_id) JOIN release_enrichments s USING(job_id) WHERE s.is_selected=1;
CREATE VIEW current_enrichment_sections AS SELECT s.* FROM enrichment_sections s JOIN current_course_enrichments c USING(job_id,course_id);
"""


def export_enrichments(root, path, source_run, ids, history=None):
    with sqlite3.connect(path) as output:
        output.execute("PRAGMA foreign_keys=ON")
        output.executescript(ENRICHMENT_SCHEMA)
        if history is None:
            history = select_enrichments(
                root,
                [r[0] for r in output.execute("SELECT run_id FROM runs")],
                ids,
                source_run,
                include_all=False,
            )
        if not history:
            return
        db = sqlite3.connect(
            (Path(root) / "processing.sqlite").resolve().as_uri() + "?mode=ro", uri=True
        )
        db.row_factory = sqlite3.Row
        try:
            db.execute("BEGIN")
            for stamp in history:
                job = stamp["job_id"]
                row = db.execute("SELECT * FROM jobs WHERE job_id=?", (job,)).fetchone()
                if (
                    not row
                    or row["status"] != "complete"
                    or job_stamp(db, row)
                    != {k: v for k, v in stamp.items() if k != "selected"}
                ):
                    raise ValueError(
                        "Enrichment changed after release history was selected"
                    )
                spec = json.loads(row["spec_json"])
                spec["profile"].pop("base_url", None)
                output.execute(
                    "INSERT INTO enrichment_jobs VALUES(?,?,?,?,?,?,?)",
                    (
                        job,
                        row["source_run"],
                        spec["task"]["name"],
                        canonical(spec),
                        spec["selected_courses"],
                        spec["total_courses"],
                        row["created_at"],
                    ),
                )
                output.execute(
                    "INSERT INTO release_enrichments VALUES(?,?)",
                    (job, int(stamp["selected"])),
                )
                for result in db.execute(
                    "SELECT * FROM results WHERE job_id=? ORDER BY course_id", (job,)
                ):
                    fields = (
                        spec["profile"]["model"],
                        spec["profile"]["revision"],
                        result["output_json"],
                        result["usage_json"],
                    )
                    identifier = digest(fields)
                    output.execute(
                        "INSERT OR IGNORE INTO enrichment_outputs VALUES(?,?,?,?,?)",
                        (identifier, *fields),
                    )
                    output.execute(
                        "INSERT INTO course_enrichment_runs VALUES(?,?,?,?)",
                        (job, row["source_run"], result["course_id"], identifier),
                    )
                    for name, section in (
                        json.loads(result["output_json"]).get("sections", {}).items()
                    ):
                        output.execute(
                            "INSERT OR IGNORE INTO enrichment_output_sections VALUES(?,?,?,?,?,?)",
                            (
                                identifier,
                                name,
                                section["status"],
                                canonical(section["value"])
                                if section.get("value") is not None
                                else None,
                                canonical(section["candidate"])
                                if section.get("candidate") is not None
                                else None,
                                section.get("error"),
                            ),
                        )
        finally:
            db.close()
        if output.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("Enrichment references missing course snapshots")
