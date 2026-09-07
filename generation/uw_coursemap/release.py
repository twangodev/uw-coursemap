"""Relational public snapshots, Parquet exports, and verified HF publication."""

import hashlib
import json
import shutil
import sqlite3
from pathlib import Path

from . import SCHEMA_VERSION
from .models import canonical
from .store import SOURCES


def checksum(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def validate(store, run, derived=False):
    info = store.run(run)
    if info["origin"] == "legacy":
        from .legacy import legacy_state

        state = legacy_state(store, run)
        if not state["courses"] or not state["instructors"]:
            raise ValueError("Legacy snapshot is missing core records")
        return dict(
            store.db.execute(
                "SELECT kind,count(*) FROM observations WHERE run_id=? GROUP BY kind",
                (run,),
            )
        )
    errors = []
    required_sources = json.loads(info["config_json"]).get("sources", list(SOURCES))
    for source in required_sources:
        if store.stage_status(run, source) != "complete":
            errors.append(f"Source {source} is incomplete")
    counts = dict(
        store.db.execute(
            "SELECT kind,count(*) FROM observations WHERE run_id=? GROUP BY kind",
            (run,),
        )
    )
    required_kinds = ["courses", "subjects", "terms", "grades", "offerings"]
    if "instructors" in required_sources:
        required_kinds.extend(["faculty", "ratings"])
    for required in required_kinds:
        if not counts.get(required):
            errors.append(f"No {required} records")
    courses = store.records(run, "courses")
    subjects = store.records(run, "subjects")
    for key, course in courses.items():
        for subject in course["course_reference"]["subjects"]:
            if subject not in subjects:
                errors.append(f"{key} references missing subject {subject}")
    if info["semester"] not in store.records(run, "terms", "enrollment"):
        errors.append("Target semester is missing")
    previous = store.db.execute(
        "SELECT run_id FROM runs WHERE status='complete' AND origin='scrape' AND run_id!=? AND observed_at<=? ORDER BY observed_at DESC LIMIT 1",
        (run, info["observed_at"]),
    ).fetchone()
    if previous:
        old = dict(
            store.db.execute(
                "SELECT kind,count(*) FROM observations WHERE run_id=? GROUP BY kind",
                (previous[0],),
            )
        )
        for kind in ("courses", "subjects", "grades", "faculty"):
            if kind in required_kinds and counts.get(kind, 0) < old.get(kind, 0) * 0.9:
                errors.append(
                    f"{kind} count fell by more than 10% ({old[kind]} -> {counts.get(kind, 0)})"
                )
    if derived:
        if store.stage_status(run, "derive") != "complete":
            errors.append("Derived stages are incomplete")
        else:
            state = store.get_artifact(run, "graph")
            if not state["instructors"]:
                errors.append("No reconciled instructors")
            if not any(state["meetings"].values()):
                errors.append("No target-semester meetings")
            total = counts.get("offerings", 0)
            if len(state["unmatched"]["offerings"]) > total * 0.1:
                errors.append("More than 10% of offerings do not match catalog courses")
    if errors:
        raise ValueError("Validation failed:\n" + "\n".join(errors[:25]))
    return counts


PUBLIC_SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE runs(run_id TEXT PRIMARY KEY,semester TEXT NOT NULL,observed_at TEXT NOT NULL,origin TEXT NOT NULL,source_revision TEXT);
CREATE TABLE observations(run_id TEXT REFERENCES runs,source TEXT,kind TEXT,entity_id TEXT,source_url TEXT,observed_at TEXT,content_hash TEXT,payload_json TEXT,PRIMARY KEY(run_id,source,kind,entity_id));
CREATE TABLE subjects(run_id TEXT REFERENCES runs,subject_id TEXT,name TEXT NOT NULL,PRIMARY KEY(run_id,subject_id));
CREATE TABLE course_versions(version_id TEXT PRIMARY KEY,course_number INTEGER NOT NULL,title TEXT NOT NULL,description TEXT NOT NULL,prerequisites_json TEXT,record_json TEXT NOT NULL);
CREATE TABLE course_snapshots(run_id TEXT REFERENCES runs,course_id TEXT,version_id TEXT NOT NULL REFERENCES course_versions,PRIMARY KEY(run_id,course_id));
CREATE INDEX course_snapshots_course ON course_snapshots(course_id,run_id);
CREATE VIEW courses AS SELECT s.run_id,s.course_id,v.course_number,v.title,v.description,v.prerequisites_json FROM course_snapshots s JOIN course_versions v USING(version_id);
CREATE VIEW course_history AS SELECT s.run_id,s.course_id,s.version_id,r.semester,r.observed_at,r.origin,r.source_revision,v.course_number,v.title,v.description,v.prerequisites_json,v.record_json FROM course_snapshots s JOIN course_versions v USING(version_id) JOIN runs r USING(run_id);
CREATE TABLE course_subjects(run_id TEXT,course_id TEXT,subject_id TEXT,PRIMARY KEY(run_id,course_id,subject_id),FOREIGN KEY(run_id,course_id) REFERENCES course_snapshots,FOREIGN KEY(run_id,subject_id) REFERENCES subjects);
CREATE TABLE terms(run_id TEXT REFERENCES runs,term_id TEXT,name TEXT NOT NULL,PRIMARY KEY(run_id,term_id));
CREATE TABLE instructors(run_id TEXT REFERENCES runs,instructor_id TEXT,name TEXT,email TEXT,official_name TEXT,department TEXT,position TEXT,details_json TEXT,PRIMARY KEY(run_id,instructor_id));
CREATE TABLE grades(run_id TEXT,course_id TEXT,term_id TEXT,distribution_json TEXT NOT NULL,PRIMARY KEY(run_id,course_id,term_id),FOREIGN KEY(run_id,course_id) REFERENCES course_snapshots,FOREIGN KEY(run_id,term_id) REFERENCES terms);
CREATE TABLE offerings(run_id TEXT REFERENCES runs,offering_id TEXT,term_id TEXT,course_id TEXT,source_course_id TEXT,source_subject_id TEXT,course_reference_json TEXT,details_json TEXT,PRIMARY KEY(run_id,offering_id),FOREIGN KEY(run_id,term_id) REFERENCES terms,FOREIGN KEY(run_id,course_id) REFERENCES course_snapshots);
CREATE TABLE sections(run_id TEXT,offering_id TEXT,section_id TEXT,section_type TEXT,section_number TEXT,details_json TEXT,PRIMARY KEY(run_id,offering_id,section_id),FOREIGN KEY(run_id,offering_id) REFERENCES offerings);
CREATE TABLE section_instructors(run_id TEXT,offering_id TEXT,section_id TEXT,instructor_name TEXT,instructor_id TEXT,PRIMARY KEY(run_id,offering_id,section_id,instructor_name),FOREIGN KEY(run_id,offering_id,section_id) REFERENCES sections,FOREIGN KEY(run_id,instructor_id) REFERENCES instructors);
CREATE TABLE meetings(run_id TEXT,course_id TEXT,meeting_id TEXT,start_time INTEGER,end_time INTEGER,details_json TEXT,PRIMARY KEY(run_id,course_id,meeting_id),FOREIGN KEY(run_id,course_id) REFERENCES course_snapshots);
CREATE TABLE derived_artifacts(run_id TEXT REFERENCES runs,name TEXT,input_hash TEXT,config_json TEXT,payload_json TEXT,PRIMARY KEY(run_id,name));
"""


def snapshot_state(store, run):
    if store.run(run)["origin"] == "legacy":
        from .legacy import legacy_state

        return legacy_state(store, run)
    for name in ("graph", "source_state"):
        row = store.db.execute(
            "SELECT payload_json FROM artifacts WHERE run_id=? AND name=?", (run, name)
        ).fetchone()
        if row:
            return json.loads(row[0])
    raise ValueError("Snapshot has no reconciled source state")


def write_database(store, run, path, state_override=None):
    public = sqlite3.connect(path)
    public.executescript(PUBLIC_SCHEMA)
    history = [
        row[0]
        for row in store.db.execute(
            "SELECT run_id FROM runs WHERE status='complete' OR run_id=? ORDER BY observed_at,run_id",
            (run,),
        )
    ]
    with public:
        for identifier in history:
            info = store.run(identifier)
            public.execute(
                "INSERT INTO runs VALUES(?,?,?,?,?)",
                (
                    identifier,
                    info["semester"],
                    info["observed_at"],
                    info["origin"],
                    info["source_revision"],
                ),
            )
            public.executemany(
                "INSERT INTO observations VALUES(?,?,?,?,?,?,?,?)",
                [
                    tuple(row)
                    for row in store.db.execute(
                        "SELECT * FROM observations WHERE run_id=? ORDER BY source,kind,entity_id",
                        (identifier,),
                    )
                ],
            )
            subjects = store.records(identifier, "subjects")
            public.executemany(
                "INSERT INTO subjects VALUES(?,?,?)",
                [(identifier, k, v["name"]) for k, v in subjects.items()],
            )
            for key, value in store.records(identifier, "courses").items():
                from .history import write_course

                write_course(public, identifier, key, value)
                public.executemany(
                    "INSERT INTO course_subjects VALUES(?,?,?)",
                    [
                        (identifier, key, s)
                        for s in value["course_reference"]["subjects"]
                    ],
                )
            public.executemany(
                "INSERT INTO terms VALUES(?,?,?)",
                [
                    (identifier, k, v["name"])
                    for k, v in store.records(identifier, "terms").items()
                ],
            )
            if identifier == run and state_override is not None:
                state = state_override
            elif info["origin"] == "legacy":
                from .legacy import legacy_state

                state = legacy_state(store, identifier)
            else:
                state = snapshot_state(store, identifier)
            for key, value in state["instructors"].items():
                public.execute(
                    "INSERT INTO instructors VALUES(?,?,?,?,?,?,?,?)",
                    (
                        identifier,
                        key,
                        value["name"],
                        value["email"],
                        value["official_name"],
                        value["department"],
                        value["position"],
                        canonical(value),
                    ),
                )
            for key, value in state["courses"].items():
                for term, term_data in value["term_data"].items():
                    if term_data["grade_data"]:
                        public.execute(
                            "INSERT INTO grades VALUES(?,?,?,?)",
                            (identifier, key, term, canonical(term_data["grade_data"])),
                        )
            aliases = {
                (subject, value["course_reference"]["course_number"]): key
                for key, value in state["courses"].items()
                for subject in value["course_reference"]["subjects"]
            }
            for key, value in store.records(identifier, "offerings").items():
                hit = value["hit"]
                public.execute(
                    "INSERT INTO offerings VALUES(?,?,?,?,?,?,?,?)",
                    (
                        identifier,
                        key,
                        value["term"],
                        next(
                            (
                                aliases[
                                    (
                                        subject,
                                        value["course_reference"]["course_number"],
                                    )
                                ]
                                for subject in value["course_reference"]["subjects"]
                                if (subject, value["course_reference"]["course_number"])
                                in aliases
                            ),
                            None,
                        ),
                        str(hit["courseId"]),
                        str(hit["subject"]["subjectCode"]),
                        canonical(value["course_reference"]),
                        canonical(hit),
                    ),
                )
                for package in value["sections"]:
                    for section in package["sections"]:
                        sid = f"{section['type']}:{section['sectionNumber']}"
                        public.execute(
                            "INSERT OR IGNORE INTO sections VALUES(?,?,?,?,?,?)",
                            (
                                identifier,
                                key,
                                sid,
                                section["type"],
                                str(section["sectionNumber"]),
                                canonical(section),
                            ),
                        )
                        from sanitization import sanitize_instructor_id

                        for instructor in section.get("instructors", []):
                            name = f"{instructor['name']['first']} {instructor['name']['last']}"
                            instructor_id = sanitize_instructor_id(name)
                            if instructor_id not in state["instructors"]:
                                instructor_id = None
                            public.execute(
                                "INSERT OR IGNORE INTO section_instructors VALUES(?,?,?,?,?)",
                                (identifier, key, sid, name, instructor_id),
                            )
            for key, meetings in state["meetings"].items():
                for meeting in meetings:
                    encoded = canonical(meeting)
                    public.execute(
                        "INSERT INTO meetings VALUES(?,?,?,?,?,?)",
                        (
                            identifier,
                            key,
                            hashlib.sha256(encoded.encode()).hexdigest(),
                            meeting["start_time"],
                            meeting["end_time"],
                            encoded,
                        ),
                    )
            public.executemany(
                "INSERT INTO derived_artifacts VALUES(?,?,?,?,?)",
                [
                    tuple(row)
                    for row in store.db.execute(
                        "SELECT * FROM artifacts WHERE run_id=? ORDER BY name",
                        (identifier,),
                    )
                ],
            )
        # No private run config, filesystem paths, request credentials or logs are exported.
        for table in (
            "courses",
            "subjects",
            "course_subjects",
            "terms",
            "instructors",
            "grades",
            "offerings",
            "sections",
            "section_instructors",
            "meetings",
            "observations",
            "derived_artifacts",
        ):
            public.execute(
                f"CREATE VIEW current_{table} AS SELECT * FROM {table} WHERE run_id='{run}'"
            )
    if public.execute("PRAGMA foreign_key_check").fetchall():
        raise ValueError("Public snapshot contains broken references")
    if public.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise ValueError("Public snapshot failed integrity check")
    public.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
    public.close()


def write_parquet(database, directory):
    import pyarrow as pa
    import pyarrow.parquet as pq

    directory.mkdir()
    db = sqlite3.connect(database)
    tables = [
        r[0]
        for r in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
    ]
    counts = {}
    for name in tables:
        columns = db.execute(f"PRAGMA table_info({name})").fetchall()
        schema = pa.schema(
            [
                (column[1], pa.int64() if column[2] == "INTEGER" else pa.string())
                for column in columns
            ]
        )
        cursor = db.execute(f"SELECT * FROM {name} ORDER BY rowid")
        counts[name] = 0
        with pq.ParquetWriter(
            directory / f"{name}.parquet", schema, compression="zstd"
        ) as writer:
            while rows := cursor.fetchmany(1000):
                writer.write_table(
                    pa.Table.from_pylist(
                        [dict(zip(schema.names, row)) for row in rows], schema=schema
                    )
                )
                counts[name] += len(rows)
        if pq.read_metadata(directory / f"{name}.parquet").num_rows != counts[name]:
            raise ValueError(f"Parquet row count mismatch: {name}")
    db.close()
    return counts


def export(store, run):
    if store.run(run)["origin"] == "legacy":
        raise ValueError(
            "Legacy history is included in fresh scrape releases; it cannot produce a standalone website release"
        )
    validate(store, run, derived=True)
    target = store.root / "releases" / run
    if target.exists():
        manifest = verify_release(target)
        if manifest["run_id"] != run or manifest["input_hash"] != store.input_hash(run):
            raise ValueError("Existing release does not match this run's observations")
        return target
    staging = target.with_name(run + ".partial")
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    write_database(store, run, staging / "coursemap.sqlite")
    counts = write_parquet(staging / "coursemap.sqlite", staging / "tables")
    from .derive import write_compatibility

    site = staging / "site"
    site.mkdir()
    write_compatibility(store, run, site)
    # Hash partition preserves logical paths without exceeding HF folder limits.
    for path in sorted(site.rglob("*")):
        if path.is_file():
            logical = path.relative_to(site).as_posix()
            destination = (
                staging
                / "web"
                / hashlib.sha256(logical.encode()).hexdigest()[:2]
                / logical
            )
            destination.parent.mkdir(parents=True, exist_ok=True)
            path.replace(destination)
    shutil.rmtree(site)
    configs = "\n".join(
        f"- config_name: {name}\n  data_files: tables/{name}.parquet" for name in counts
    )
    (staging / "README.md").write_text(
        f"---\nconfigs:\n{configs}\n---\n\n# UW Course Map\n\nSemester {store.run(run)['semester']}. Run `{run}`.\n\nSQLite and Parquet contain the same relational tables, including scrape history.\nJoin on `run_id` plus entity IDs; SQLite `current_*` views select this release.\n`observations` preserves source URLs, observation times, hashes, and original parsed records.\nJSON columns retain nested source fields, grade distributions, prerequisite trees, and derived details.\n`grades` contains per-term distributions; cumulative grades are retained in derived artifacts.\n`sections` and `meetings` retain instructor and location details in JSON.\nSources: UW Guide, UW public enrollment API, Madgrades, and Rate My Professors.\nMeetings are a snapshot, not a live schedule. Source data and model output may contain errors.\nExisting website files are under `web/<sha256(logical_path)[:2]>/<logical_path>`.\n"
    )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run,
        "semester": store.run(run)["semester"],
        "observed_at": store.run(run)["observed_at"],
        "input_hash": store.input_hash(run),
        "tables": counts,
        "files": {
            p.relative_to(staging).as_posix(): {
                "sha256": checksum(p),
                "bytes": p.stat().st_size,
            }
            for p in sorted(staging.rglob("*"))
            if p.is_file()
        },
    }
    (staging / "manifest.json").write_text(canonical(manifest))
    verify_release(staging)
    staging.replace(target)
    return target


def verify_release(directory):
    manifest = json.loads((directory / "manifest.json").read_text())
    actual = {
        p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()
    }
    if actual != set(manifest["files"]) | {"manifest.json"}:
        raise ValueError("Release contains missing or unexpected files")
    for name, metadata in manifest["files"].items():
        path = directory / name
        if path.is_symlink() or not path.resolve().is_relative_to(directory.resolve()):
            raise ValueError("Invalid release path")
        if (
            path.stat().st_size != metadata["bytes"]
            or checksum(path) != metadata["sha256"]
        ):
            raise ValueError(f"Release checksum mismatch: {name}")
    return manifest


def publish(store, run, repo_id, api=None, download=None):
    from huggingface_hub import (
        HfApi,
        CommitOperationAdd,
        CommitOperationDelete,
        hf_hub_download,
    )

    directory = store.root / "releases" / run
    manifest = verify_release(directory)
    source_run = manifest.get("source_run", run)
    if store.run(source_run)["status"] != "complete" or manifest[
        "input_hash"
    ] != store.input_hash(source_run):
        raise ValueError("Only a completed, unchanged run can be published")
    api = api or HfApi()
    download = download or hf_hub_download
    api.create_repo(repo_id=repo_id, repo_type="dataset", private=False, exist_ok=True)
    branch = f"runs/{run}"
    tag = f"release-{run}"
    expected = sorted(set(manifest["files"]) | {"manifest.json"})
    checkpoint_path = (
        store.root
        / "runs"
        / run
        / ("upload-" + hashlib.sha256(repo_id.encode()).hexdigest() + ".json")
    )
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_hash = checksum(directory / "manifest.json")
    base = api.repo_info(repo_id=repo_id, repo_type="dataset", revision="main").sha
    api.create_branch(
        repo_id=repo_id, repo_type="dataset", branch=branch, exist_ok=True
    )
    head = api.repo_info(repo_id=repo_id, repo_type="dataset", revision=branch).sha
    checkpoint = {
        "index": 0,
        "revision": head,
        "base": base,
        "manifest_hash": manifest_hash,
    }
    if checkpoint_path.exists():
        checkpoint = json.loads(checkpoint_path.read_text())
        if checkpoint["manifest_hash"] != manifest_hash:
            raise ValueError("Release changed after publication started")
        if checkpoint.get("complete"):
            return {"repo_id": repo_id, "revision": checkpoint["revision"], "tag": tag}
        if checkpoint["revision"] != head:
            # Commit succeeded but the process died before its checkpoint: replay
            # the idempotent uploads against the current branch head.
            checkpoint.update(index=0, revision=head)

    def save_checkpoint():
        temporary = checkpoint_path.with_suffix(".tmp")
        temporary.write_text(canonical(checkpoint))
        temporary.replace(checkpoint_path)

    remote = set(
        api.list_repo_files(repo_id=repo_id, repo_type="dataset", revision=head)
    )
    deletes = sorted(remote - set(expected) - {".gitattributes"})
    for offset in range(0, len(deletes), 100):
        commit = api.create_commit(
            repo_id=repo_id,
            repo_type="dataset",
            revision=branch,
            parent_commit=checkpoint["revision"],
            operations=[
                CommitOperationDelete(name) for name in deletes[offset : offset + 100]
            ],
            commit_message="Remove files outside this snapshot",
        )
        checkpoint["revision"] = commit.oid
        save_checkpoint()
    for offset in range(checkpoint["index"], len(expected), 100):
        commit = api.create_commit(
            repo_id=repo_id,
            repo_type="dataset",
            revision=branch,
            parent_commit=checkpoint["revision"],
            operations=[
                CommitOperationAdd(name, str(directory / name))
                for name in expected[offset : offset + 100]
            ],
            commit_message=f"Upload {run}: files {offset + 1}-{min(offset + 100, len(expected))}",
        )
        checkpoint.update(index=min(offset + 100, len(expected)), revision=commit.oid)
        save_checkpoint()
    revision = checkpoint["revision"]
    remote = set(
        api.list_repo_files(repo_id=repo_id, repo_type="dataset", revision=revision)
    )
    if remote - {".gitattributes"} != set(expected):
        raise ValueError("Remote release file list differs")
    downloaded = download(
        repo_id, "manifest.json", repo_type="dataset", revision=revision
    )
    if Path(downloaded).read_bytes() != (directory / "manifest.json").read_bytes():
        raise ValueError("Remote release manifest differs")
    api.create_tag(
        repo_id=repo_id, repo_type="dataset", tag=tag, revision=revision, exist_ok=True
    )
    if (
        api.repo_info(repo_id=repo_id, repo_type="dataset", revision=tag).sha
        != revision
    ):
        raise ValueError("Release tag already points to a different revision")
    # A single pointer commit activates only a complete immutable snapshot. An
    # intervening publication causes a conflict instead of silently replacing it.
    pointer = canonical(
        {
            "run_id": run,
            "revision": revision,
            "tag": tag,
            "manifest_sha256": manifest_hash,
        }
    ).encode()
    latest = api.repo_info(repo_id=repo_id, repo_type="dataset", revision="main").sha
    if latest != checkpoint["base"]:
        try:
            current = Path(
                download(repo_id, "latest.json", repo_type="dataset", revision=latest)
            ).read_bytes()
        except Exception as exc:
            raise ValueError(
                "HF main changed during upload; latest was not replaced"
            ) from exc
        if current != pointer:
            raise ValueError(
                "Another release advanced HF main; latest was not replaced"
            )
    else:
        api.create_commit(
            repo_id=repo_id,
            repo_type="dataset",
            revision="main",
            parent_commit=checkpoint["base"],
            operations=[CommitOperationAdd("latest.json", pointer)],
            commit_message=f"Activate validated release {run}",
        )
    if "source_run" not in manifest:
        with store.db:
            store.db.execute(
                "UPDATE runs SET revision=? WHERE run_id=?", (revision, source_run)
            )
    checkpoint["complete"] = True
    save_checkpoint()
    return {"repo_id": repo_id, "revision": revision, "tag": tag}
