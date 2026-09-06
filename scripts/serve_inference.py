"""Launch one isolated vLLM server using a scrape run's pinned model revision."""

import argparse
import json
import os
from pathlib import Path
import sqlite3
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--run", required=True)
    parser.add_argument("--kind", required=True, choices=["embedding", "keyword"])
    args = parser.parse_args()
    with sqlite3.connect(
        f"file:{args.workspace.resolve() / 'pipeline.sqlite'}?mode=ro", uri=True
    ) as db:
        row = db.execute(
            "SELECT config_json FROM runs WHERE run_id=?", (args.run,)
        ).fetchone()
    if row is None:
        raise ValueError("Unknown scrape run")
    config = json.loads(row[0])
    model, revision = config[f"{args.kind}_model"], config[f"{args.kind}_revision"]
    env = dict(os.environ)
    # Keep vLLM's dependency graph independent of the scraper's environment.
    env.pop("UV_PROJECT_ENVIRONMENT", None)
    env.pop("VIRTUAL_ENV", None)
    env["UV_PROJECT_ENVIRONMENT"] = str(args.workspace.resolve() / "inference-venv")
    env["HF_HOME"] = str(args.workspace.resolve() / "models" / "huggingface")
    env["XDG_CACHE_HOME"] = str(args.workspace.resolve() / "runtime-cache")
    env["VLLM_NO_USAGE_STATS"] = "1"
    if env.get("COURSEMAP_INFERENCE_API_KEY"):
        env["VLLM_API_KEY"] = env["COURSEMAP_INFERENCE_API_KEY"]
    command = [
        "uv",
        "run",
        "--project",
        str(Path(__file__).resolve().parents[1] / "inference"),
        "--locked",
        "vllm",
        "serve",
        model,
        "--revision",
        revision,
        "--tokenizer-revision",
        revision,
        "--served-model-name",
        f"{model}@{revision}",
        "--runner",
        "pooling",
        "--pooler-config",
        '{"pooling_type":"MEAN","use_activation":true}',
        "--host",
        "127.0.0.1",
        "--port",
        "8001" if args.kind == "embedding" else "8002",
        "--gpu-memory-utilization",
        "0.15",
        "--max-model-len",
        "512" if args.kind == "embedding" else "256",
        "--enforce-eager",
    ]
    subprocess.run(command, env=env, check=True)


if __name__ == "__main__":
    main()
