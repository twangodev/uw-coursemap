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
        metavar="{run,resume,status,validate,export,publish,replay}",
    )
    run = commands.add_parser("run", help="Create and execute a fresh semester scrape")
    run.add_argument(
        "--semester", required=True, help="UW numeric term code, e.g. 1272"
    )
    run.add_argument("--sitemap-base", default="https://uwcourses.com")
    run.add_argument("--max-prerequisites", type=int, default=1)
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
        if name == "replay":
            command.add_argument("--source", choices=SOURCES, required=True)
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
    # Explicit environment configuration; never load arbitrary repository .env files.
    if args.command == "_crawl":
        from .crawl import crawl

        crawl(args.workspace, args.run_id, args.source, args.offline)
        return
    store = Store(args.workspace)
    try:
        if args.command == "status":
            info = store.run(args.run_id)
            print(
                canonical(
                    {
                        "run_id": info["run_id"],
                        "semester": info["semester"],
                        "status": info["status"],
                        "revision": info["revision"],
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
            if args.command == "run":
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
                from huggingface_hub import HfApi

                api = HfApi()
                from http_utils import get_user_agent

                config = {
                    "user_agent": get_user_agent(),
                    "code_hash": code_hash(),
                    "sitemap_base": args.sitemap_base,
                    "max_prerequisites": args.max_prerequisites,
                    "embedding_model": "avsolatorio/GIST-large-Embedding-v0",
                    "keyword_model": "sentence-transformers/all-MiniLM-L6-v2",
                }
                config["embedding_revision"] = api.model_info(
                    config["embedding_model"]
                ).sha
                config["keyword_revision"] = api.model_info(config["keyword_model"]).sha
                run = store.new_run(args.semester, config)
                print(f"Created run {run}", flush=True)
                result = execute(store, run)
            elif args.command == "resume":
                result = execute(store, args.run_id)
            elif args.command == "validate":
                from .release import validate

                result = validate(
                    store,
                    args.run_id,
                    derived=store.stage_status(args.run_id, "derive") == "complete",
                )
            elif args.command == "export":
                from .release import export

                result = {"release": str(export(store, args.run_id))}
            elif args.command == "publish":
                from .release import publish

                result = publish(store, args.run_id, args.repo)
            elif args.command == "replay":
                info = store.run(args.run_id)
                config = json.loads(info["config_json"])
                config.update(code_hash=code_hash(), replay_from=args.run_id)
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
