"""Command-line entry point; each crawl runs in its own Scrapy process."""

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from .models import canonical
from .store import SOURCES, Store


def parser():
    root = argparse.ArgumentParser(prog="coursemap")
    root.add_argument(
        "--workspace",
        type=Path,
        default=Path(os.environ.get("COURSEMAP_WORKSPACE", "./.coursemap")),
    )
    commands = root.add_subparsers(
        dest="command",
        required=True,
    )
    run = commands.add_parser(
        "scrape",
        aliases=["run"],
        help="Create an immutable source snapshot; no model inference",
    )
    run.add_argument(
        "--semester", required=True, help="UW numeric term code, e.g. 1272"
    )
    run.add_argument("--concurrency", type=int, default=32)
    run.add_argument("--per-domain", type=int, default=16)
    run.add_argument("--target-concurrency", type=float, default=8)
    run.add_argument("--download-delay", type=float, default=0.1)
    run.add_argument("--sitemap-base", default="https://uwcourses.com")
    run.add_argument("--max-prerequisites", type=int, default=1)
    run.add_argument(
        "--include-instructors",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    for name in ("derive", "enrich", "release"):
        command = commands.add_parser(name)
        command.add_argument("run_id")
        if name in ("derive", "enrich"):
            command.add_argument("--models-config", type=Path, required=True)
        if name == "enrich":
            command.add_argument("--prepare-only", action="store_true")
            command.add_argument("--reuse-job", action="append", default=[])
            command.add_argument(
                "--allow-partial-reuse",
                action="store_true",
                help="Snapshot completed student-summary results from unfinished reuse jobs",
            )
            command.add_argument("--profile", default="enrichment")
            command.add_argument("--task", type=Path, required=True)
            command.add_argument(
                "--course",
                action="append",
                help="Explicit course ID or alias; repeat for a targeted test",
            )
            command.add_argument(
                "--limit",
                type=int,
                default=100,
                help="Stable sample size; 0 processes all courses",
            )
        if name == "release":
            command.add_argument("--build")
            command.add_argument("--enrichment", action="append", default=[])
    for name in ("enrich-resume", "job-status", "job-report", "derive-resume"):
        command = commands.add_parser(name)
        command.add_argument("job_id")
        if name == "enrich-resume":
            command.add_argument("--concurrency", type=int)
            command.add_argument("--request-timeout-seconds", type=int)
    repair = commands.add_parser(
        "enrich-repair",
        help="Repair saved rejected sections through validator conversation turns",
    )
    repair.add_argument("job_id")
    repair.add_argument("--models-config", type=Path, required=True)
    repair.add_argument("--profile", default="enrichment-unified")
    repair.add_argument("--limit", type=int, default=20)
    repair.add_argument("--course", action="append")
    repair.add_argument("--turns", type=int, default=3)
    repair.add_argument("--prepare-only", action="store_true")
    repair.add_argument(
        "--task", type=Path, help="Updated repair prompt with the same output schema"
    )
    descriptions = {
        "resume": "Continue an interrupted run",
        "status": "Show source and stage completion",
        "validate": "Check source completeness and relationships",
        "export": "Build or verify a local release",
        "publish": "Upload a completed release to Hugging Face",
        "replay": "Create a new run from archived source responses",
    }
    for name, description in descriptions.items():
        command = commands.add_parser(name, help=description)
        command.add_argument("run_id")
        if name == "publish":
            command.add_argument("--repo", required=True, help="HF dataset owner/name")
            command.add_argument(
                "--parquet-only",
                action="store_true",
                help="Publish tables, card and sync metadata without SQLite or serving files",
            )
        if name == "replay":
            command.add_argument("--source", choices=SOURCES, required=True)
    refresh = commands.add_parser(
        "refresh-instructors",
        help="Collect required faculty/RMP data using an existing frozen catalog and grades",
    )
    refresh.add_argument("run_id")
    refresh.add_argument(
        "--source-workspace",
        type=Path,
        help="Optional separate source workspace; the new run is written to --workspace",
    )
    commands.add_parser(
        "public-export",
        help="Build public tables and serving files from a verified archive",
    ).add_argument("release_id")
    models = commands.add_parser("models-lock")
    models.add_argument("--models-config", type=Path, required=True)
    models.add_argument("--profile", action="append", required=True)
    models.add_argument("--output", type=Path, required=True)
    crawl = commands.add_parser("_crawl")
    crawl.add_argument("run_id")
    crawl.add_argument("source", choices=SOURCES)
    crawl.add_argument("--offline", action="store_true")
    return root


def code_hash():
    import hashlib

    directory = Path(__file__).parent
    files = sorted(directory.glob("*.py")) + sorted(directory.parent.glob("*.py"))
    hasher = hashlib.sha256()
    for path in files:
        hasher.update(path.name.encode())
        hasher.update(path.read_bytes())
    return hasher.hexdigest()


def execute_source(store, run, source, offline=False):
    store.stage(run, source, "running")
    command = [
        sys.executable,
        "-m",
        "uw_coursemap.cli",
        "--workspace",
        str(store.root),
        "_crawl",
        run,
        source,
    ]
    if offline:
        command.append("--offline")
    log = store.root / "runs" / run / f"{source}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a") as output:
        result = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT)
    if result.returncode:
        store.stage(run, source, "failed", f"See {log.name}")
        raise RuntimeError(f"{source} failed; see {log}")
    store.stage(run, source, "complete")


def execute(store, run):
    try:
        return execute_run(store, run)
    except Exception:
        with store.db:
            store.db.execute(
                "UPDATE runs SET status='failed' WHERE run_id=? AND status!='complete'",
                (run,),
            )
        raise


def execute_run(store, run):
    from .derive import derive
    from .release import export, validate

    if json.loads(store.run(run)["config_json"]).get("workflow") == "snapshot-v1":
        from .lifecycle import scrape

        return scrape(store, run)
    info = store.run(run)
    if info["status"] == "complete":
        return {"run_id": run, "status": "complete"}
    config = json.loads(info["config_json"])
    if config["code_hash"] != code_hash():
        raise ValueError(
            "Pipeline code changed; create a new run instead of mixing versions"
        )
    with store.db:
        store.db.execute("UPDATE runs SET status='running' WHERE run_id=?", (run,))
    for source in SOURCES:
        if store.stage_status(run, source) != "complete":
            print(f"Running {source} ({run})", flush=True)
            execute_source(store, run, source)
    validate(store, run)
    if store.stage_status(run, "derive") != "complete":
        store.stage(run, "derive", "running")
        try:
            derive(store, run)
        except Exception as exc:
            store.stage(run, "derive", "failed", type(exc).__name__)
            raise
        store.stage(run, "derive", "complete")
    store.stage(run, "export", "running")
    try:
        output = export(store, run)
    except Exception as exc:
        store.stage(run, "export", "failed", type(exc).__name__)
        raise
    store.stage(run, "export", "complete")
    store.finish(run)
    return {"run_id": run, "release": str(output)}


def main(argv=None):
    args = parser().parse_args(argv)
    for name in ("run_id", "job_id", "build"):
        value = getattr(args, name, None)
        if value and not re.fullmatch(r"[A-Za-z0-9_-]+", value):
            raise ValueError(f"Invalid {name}")
    if args.command == "models-lock":
        from .profiles import lock_profiles

        print(canonical(lock_profiles(args.models_config, args.profile, args.output)))
        return
    if args.command == "publish" and args.run_id.startswith("release-"):
        from .release import publish

        if args.parquet_only:
            from .publication import publish_parquet as publish
        from .jobs import file_lock

        store = Store(args.workspace, readonly=True)
        try:
            with file_lock(
                args.workspace / "releases" / (args.run_id + ".publish.lock")
            ):
                print(canonical(publish(store, args.run_id, args.repo)))
        finally:
            store.close()
        return
    # Explicit environment configuration; never load arbitrary repository .env files.
    if args.command == "_crawl":
        from .crawl import crawl

        crawl(args.workspace, args.run_id, args.source, args.offline)
        return
    if args.command == "job-report":
        from .job_report import report

        print(canonical(report(args.workspace, args.job_id)))
        return
    if args.command in {
        "derive",
        "derive-resume",
        "enrich",
        "enrich-resume",
        "enrich-repair",
        "job-status",
    }:
        from .lifecycle import build
        from .jobs import Jobs

        if args.command == "derive":
            result = build(args.workspace, args.run_id, args.models_config)
        elif args.command == "derive-resume":
            meta = json.loads(
                (args.workspace / "builds" / args.job_id / "build.json").read_text()
            )
            result = build(args.workspace, meta["source_run"], build_id=args.job_id)
        else:
            jobs = Jobs(args.workspace)
            try:
                if args.command == "enrich":
                    if args.limit < 0:
                        raise ValueError("limit must be nonnegative")
                    job = jobs.create(
                        args.run_id,
                        args.models_config,
                        args.profile,
                        args.task,
                        args.limit,
                        course_ids=args.course,
                        reuse_job_ids=args.reuse_job,
                        allow_partial_reuse=args.allow_partial_reuse,
                    )
                    print(f"Created enrichment job {job}", flush=True)
                    result = jobs.status(job) if args.prepare_only else jobs.run(job)
                elif args.command == "enrich-repair":
                    from .repair import create_repair

                    job = create_repair(
                        jobs,
                        args.job_id,
                        args.models_config,
                        args.profile,
                        args.limit,
                        args.course,
                        args.turns,
                        task_path=args.task,
                    )
                    print(f"Created repair job {job}", flush=True)
                    result = jobs.status(job) if args.prepare_only else jobs.run(job)
                elif args.command == "enrich-resume":
                    result = jobs.run(
                        args.job_id,
                        concurrency=args.concurrency,
                        request_timeout=args.request_timeout_seconds,
                    )
                else:
                    result = jobs.status(args.job_id)
            finally:
                jobs.close()
        print(canonical(result))
        return
    if args.command == "public-export":
        from .public_data import export_public

        print(
            canonical({"release": str(export_public(args.workspace, args.release_id))})
        )
        return
    readonly = args.command in {"status", "validate", "release"}
    store = Store(args.workspace, readonly=readonly)
    try:
        if args.command == "release":
            from .lifecycle import release

            print(
                canonical(
                    {
                        "release": str(
                            release(store, args.run_id, args.build, args.enrichment)
                        )
                    }
                )
            )
            return
        if args.command == "validate":
            from .release import validate

            print(
                canonical(
                    validate(
                        store,
                        args.run_id,
                        derived=store.stage_status(args.run_id, "derive") == "complete",
                    )
                )
            )
            return
        if args.command == "status":
            info = store.run(args.run_id)
            print(
                canonical(
                    {
                        "run_id": info["run_id"],
                        "semester": info["semester"],
                        "status": info["status"],
                        "revision": info["revision"],
                        "observed_at": info["observed_at"],
                        "origin": info["origin"],
                        "source_revision": info["source_revision"],
                        "stages": [
                            dict(r)
                            for r in store.db.execute(
                                "SELECT stage,status,error,updated_at FROM stages WHERE run_id=?",
                                (args.run_id,),
                            )
                        ],
                    }
                )
            )
            return
        with store.lock():
            if args.command in {"run", "scrape"}:
                if not re.fullmatch(r"\d{4}", args.semester):
                    raise ValueError("Use the four-digit UW term code")
                if args.max_prerequisites < 1:
                    raise ValueError("max-prerequisites must be positive")
                if not os.environ.get("MADGRADES_API_KEY"):
                    raise ValueError("MADGRADES_API_KEY is required")
                if shutil.disk_usage(store.root).free < 10 * 1024**3:
                    raise ValueError(
                        "At least 10 GiB free is required for a new run; model downloads may require more"
                    )
                from http_utils import get_user_agent

                config = {
                    "http": {
                        "concurrency": args.concurrency,
                        "per_domain": args.per_domain,
                        "target_concurrency": args.target_concurrency,
                        "download_delay": args.download_delay,
                    },
                    "workflow": "snapshot-v1",
                    "sources": list(SOURCES),
                    "ratings_contract": 1,
                    "user_agent": get_user_agent(),
                    "code_hash": code_hash(),
                    "sitemap_base": args.sitemap_base,
                    "max_prerequisites": args.max_prerequisites,
                }
                from .crawl import http_settings

                http_settings(config)
                run = store.new_run(args.semester, config)
                print(f"Created run {run}", flush=True)
                result = execute(store, run)
            elif args.command == "refresh-instructors":
                from .lifecycle import prepare_instructor_refresh

                run = prepare_instructor_refresh(
                    store, args.run_id, args.source_workspace
                )
                print(f"Created instructor refresh run {run}", flush=True)
                result = execute(store, run)
            elif args.command == "resume":
                result = execute(store, args.run_id)
            elif args.command == "export":
                from .release import export

                if (
                    json.loads(store.run(args.run_id)["config_json"]).get("workflow")
                    == "snapshot-v1"
                ):
                    from .lifecycle import release

                    result = {"release": str(release(store, args.run_id))}
                else:
                    result = {"release": str(export(store, args.run_id))}
            elif args.command == "publish":
                from .release import publish

                if args.parquet_only:
                    from .publication import publish_parquet as publish

                result = publish(store, args.run_id, args.repo)
            elif args.command == "replay":
                info = store.run(args.run_id)
                config = json.loads(info["config_json"])
                config.update(
                    code_hash=code_hash(),
                    replay_from=args.run_id,
                    sources=list(SOURCES),
                    ratings_contract=1,
                )
                run = store.new_run(info["semester"], config)
                with store.db:
                    store.db.execute(
                        "INSERT INTO responses SELECT ?,source,fingerprint,url,status,content_type,body_hash,fetched_at FROM responses WHERE run_id=?",
                        (run, args.run_id),
                    )
                print(f"Created replay run {run}", flush=True)
                for source in SOURCES[: SOURCES.index(args.source) + 1]:
                    execute_source(store, run, source, offline=True)
                result = {
                    "run_id": run,
                    "source": args.source,
                    "status": "complete",
                    "next": f"resume {run}",
                }
            print(canonical(result))
    finally:
        store.close()


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
