"""Independent immutable source snapshots, processing builds, and releases."""

import json
import shutil
from pathlib import Path

from .models import canonical, digest
from .store import Store, SOURCES, STAGES, now


def scrape(store, run):
    from .cli import execute_source, code_hash
    from .derive import reconcile, encode_state
    from .release import validate

    info = store.run(run)
    if info["status"] == "complete":
        return {"run_id": run, "status": "complete"}
    config = json.loads(info["config_json"])
    if config["code_hash"] != code_hash():
        raise ValueError(
            "Scraper code changed; use replay to create a snapshot with new parser provenance"
        )
    with store.db:
        store.db.execute("UPDATE runs SET status='running' WHERE run_id=?", (run,))
    failures = []
    # Independent sources continue even if another source fails.
    for source in config["sources"]:
        if store.stage_status(run, source) == "complete":
            continue
        try:
            execute_source(store, run, source)
        except RuntimeError:
            failures.append(source)
    if failures:
        with store.db:
            store.db.execute("UPDATE runs SET status='failed' WHERE run_id=?", (run,))
        raise RuntimeError(
            f"Sources failed: {', '.join(failures)}; completed sources are checkpointed"
        )
    validate(store, run)
    state = encode_state(*reconcile(store, run))
    if not state["instructors"] or not any(state["meetings"].values()):
        raise ValueError(
            "Snapshot lacks reconciled instructors or target-semester meetings"
        )
    if (
        len(state["unmatched"]["offerings"])
        > len(store.records(run, "offerings")) * 0.1
    ):
        raise ValueError("More than 10% of offerings do not match catalog courses")
    store.artifact(
        run,
        "source_state",
        state,
        store.input_hash(run),
        {"inference": False, "code_hash": config["code_hash"]},
    )
    store.finish(run)
    return {"run_id": run, "status": "complete", "next": f"release {run}"}


def require_snapshot(store, run):
    if store.run(run)["status"] != "complete":
        raise ValueError("Processing requires a completed immutable source snapshot")


def build(root, source_run, profiles=None, build_id=None):
    from .cli import code_hash
    from .derive import derive
    from .profiles import load_profile

    root = Path(root)
    source = Store(root, readonly=True)
    try:
        require_snapshot(source, source_run)
        if source.run(source_run)["origin"] == "legacy":
            raise ValueError(
                "Legacy snapshots lack raw inputs for rebuilding; release or enrich them directly"
            )
        if build_id is None:
            selected = {
                kind: load_profile(profiles, kind).model_dump()
                for kind in ("embedding", "keyword")
            }
            config = {
                **json.loads(source.run(source_run)["config_json"]),
                "model_profiles": selected,
                "code_hash": code_hash(),
                "source_run": source_run,
                "source_hash": source.input_hash(source_run),
            }
            for kind, profile in selected.items():
                config[f"{kind}_model"] = profile["model"]
                config[f"{kind}_revision"] = profile["revision"]
            config.setdefault("max_prerequisites", 1)
            config.setdefault("sitemap_base", "https://uwcourses.com")
            build_id = "build-" + digest(config)[:24]
        directory = root / "builds" / build_id
        state = Store(directory)
        try:
            with state.lock():
                meta_path = directory / "build.json"
                if meta_path.exists():
                    meta = json.loads(meta_path.read_text())
                    if meta["source_run"] != source_run:
                        raise ValueError("Build belongs to another snapshot")
                    job = meta["run_id"]
                    config = json.loads(state.run(job)["config_json"])
                else:
                    if profiles is None:
                        raise ValueError("Unknown build")
                    job = build_id
                    # The copied snapshot and checkpoints commit atomically. A crash
                    # before build.json is written can recover this deterministic job.
                    with state.db:
                        if not state.db.execute(
                            "SELECT 1 FROM runs WHERE run_id=?", (job,)
                        ).fetchone():
                            state.db.execute(
                                "INSERT INTO runs(run_id,semester,started_at,status,config_json,observed_at) VALUES(?,?,?,'pending',?,?)",
                                (
                                    job,
                                    source.run(source_run)["semester"],
                                    now(),
                                    canonical(config),
                                    source.run(source_run)["observed_at"],
                                ),
                            )
                            state.db.executemany(
                                "INSERT INTO stages VALUES(?,?,?,NULL,?)",
                                [
                                    (
                                        job,
                                        name,
                                        (
                                            source.stage_status(source_run, name)
                                            or "pending"
                                        )
                                        if name in SOURCES
                                        else "pending",
                                        now(),
                                    )
                                    for name in STAGES
                                ],
                            )
                            rows = source.db.execute(
                                "SELECT * FROM observations WHERE run_id=?",
                                (source_run,),
                            )
                            state.db.executemany(
                                "INSERT INTO observations VALUES(?,?,?,?,?,?,?,?)",
                                ((job, *tuple(row)[1:]) for row in rows),
                            )
                    meta = {
                        "build_id": build_id,
                        "source_run": source_run,
                        "run_id": job,
                    }
                    temporary = meta_path.with_suffix(".tmp")
                    temporary.write_text(canonical(meta))
                    temporary.replace(meta_path)
                if config["source_hash"] != source.input_hash(source_run):
                    raise ValueError("Source snapshot changed")
                if config["code_hash"] != code_hash():
                    raise ValueError("Build code changed; start a new build")
                if state.run(job)["status"] != "complete":
                    state.cache_root = root / "models"
                    state.stage(job, "derive", "running")
                    try:
                        derive(state, job)
                        state.stage(job, "derive", "complete")
                        from .release import validate

                        validate(state, job, derived=True)
                        state.finish(job)
                    except Exception as exc:
                        state.stage(job, "derive", "failed", type(exc).__name__)
                        raise
                return meta
        finally:
            state.close()
    finally:
        source.close()


def release(store, run, build_id=None, enrichment_ids=()):
    # One read transaction freezes the history selection while another scrape writes.
    store.db.execute("BEGIN")
    try:
        return _release(store, run, build_id, enrichment_ids)
    finally:
        store.db.rollback()


def _release(store, run, build_id, enrichment_ids):
    from .release import write_database, write_parquet, checksum, verify_release
    from . import SCHEMA_VERSION
    from .cli import code_hash
    import sqlite3

    require_snapshot(store, run)
    # Serialize release assembly without taking the source writer lock.
    from .jobs import file_lock, Jobs

    with file_lock(store.root / "releases.lock"):
        history = [
            (row["run_id"], store.input_hash(row["run_id"]))
            for row in store.db.execute(
                "SELECT run_id FROM runs WHERE status='complete' ORDER BY run_id"
            )
        ]
        selection = {
            "source_run": run,
            "history": history,
            "build_id": build_id,
            "enrichment_ids": sorted(set(enrichment_ids)),
            "schema_version": SCHEMA_VERSION,
            "exporter_hash": code_hash(),
        }
        release_id = "release-" + digest(selection)[:24]
        target = store.root / "releases" / release_id
        if target.exists():
            verify_release(target)
            return target
        staging = target.with_name(target.name + ".partial")
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir(parents=True)
        build_store = None
        state = None
        try:
            if build_id:
                directory = store.root / "builds" / build_id
                meta = json.loads((directory / "build.json").read_text())
                if meta["source_run"] != run:
                    raise ValueError("Build belongs to another snapshot")
                build_store = Store(directory, readonly=True)
                require_snapshot(build_store, meta["run_id"])
                state = build_store.get_artifact(meta["run_id"], "graph")
            write_database(
                store, run, staging / "coursemap.sqlite", state_override=state
            )
            with sqlite3.connect(staging / "coursemap.sqlite") as public:
                public.execute(
                    "CREATE TABLE processing_builds(build_id TEXT PRIMARY KEY,run_id TEXT REFERENCES runs,config_json TEXT NOT NULL)"
                )
                if build_store:
                    config = json.loads(build_store.run(meta["run_id"])["config_json"])
                    for profile in config.get("model_profiles", {}).values():
                        profile.pop("base_url", None)
                    public.execute(
                        "INSERT INTO processing_builds VALUES(?,?,?)",
                        (build_id, run, canonical(config)),
                    )
                    for artifact in build_store.db.execute(
                        "SELECT name,input_hash,config_json,payload_json FROM artifacts WHERE run_id=?",
                        (meta["run_id"],),
                    ):
                        public.execute(
                            "INSERT INTO derived_artifacts VALUES(?,?,?,?,?)",
                            (
                                run,
                                build_id + "/" + artifact["name"],
                                artifact["input_hash"],
                                canonical(config),
                                artifact["payload_json"],
                            ),
                        )
            Jobs.append_release(
                store.root, staging / "coursemap.sqlite", run, enrichment_ids
            )
            counts = write_parquet(staging / "coursemap.sqlite", staging / "tables")
            if build_store:
                from .derive import write_compatibility

                write_compatibility(build_store, meta["run_id"], staging / "site")
                for path in sorted((staging / "site").rglob("*")):
                    if path.is_file():
                        import hashlib

                        logical = path.relative_to(staging / "site").as_posix()
                        destination = (
                            staging
                            / "web"
                            / hashlib.sha256(logical.encode()).hexdigest()[:2]
                            / logical
                        )
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        path.replace(destination)
                shutil.rmtree(staging / "site")
            configs = "\n".join(
                f"- config_name: {name}\n  data_files: tables/{name}.parquet"
                for name in counts
            )
            with sqlite3.connect(staging / "coursemap.sqlite") as public:
                model_profiles = [
                    json.loads(row[0])["profile"]
                    for row in public.execute(
                        "SELECT spec_json FROM enrichment_jobs ORDER BY job_id"
                    )
                ]
            model_ids = sorted(
                {
                    f"{profile['model']}@{profile['revision']}"
                    for profile in model_profiles
                }
            )
            model_citations = "\n".join(f"- `{identity}`" for identity in model_ids)
            (staging / "README.md").write_text(
                f"---\nconfigs:\n{configs}\n---\n\n# UW Course Map\n\nSource snapshot `{run}`. SQLite and Parquet contain equivalent tables.\nJoin observations by run_id; never sum cumulative grade snapshots across runs.\nGenerated course enrichments are separate, model-produced data, not official catalog facts.\nSee manifest.json for selected build, enrichment coverage, and provenance.\n"
                + (
                    f"\nGeneration models (pinned revisions):\n\n{model_citations}\n\n"
                    if model_ids
                    else ""
                )
                + "`enrichment_sections` contains independently validated sections, exact model/revision fields, and rejected candidates. Filter by section status; completed jobs can contain invalid or review-required sections. Full settings, local lookup traces, dependency hashes, and original requirement trees are retained in `enrichment_jobs` and `course_enrichments`.\n"
            )
            manifest = {
                **selection,
                "run_id": release_id,
                "input_hash": store.input_hash(run),
                "observed_at": store.run(run)["observed_at"],
                "tables": counts,
                "website_included": bool(build_id),
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
        finally:
            if build_store:
                build_store.close()
