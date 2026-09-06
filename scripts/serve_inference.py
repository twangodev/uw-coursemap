"""Launch an isolated vLLM server from a locked model profile."""

import argparse
import json
import os
from pathlib import Path
import sqlite3
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--models-config", type=Path)
    selection.add_argument("--run", help="Compatibility with older combined runs")
    parser.add_argument("--profile", default="enrichment")
    parser.add_argument("--kind", choices=["embedding", "keyword"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    from uw_coursemap.profiles import ModelProfile, load_profile
    from urllib.parse import urlparse

    if args.models_config:
        profile = load_profile(args.models_config, args.profile, resolve=False)
    else:
        if not args.kind:
            parser.error("--run requires --kind")
        with sqlite3.connect(
            (args.workspace.resolve() / "pipeline.sqlite").as_uri() + "?mode=ro",
            uri=True,
        ) as db:
            row = db.execute(
                "SELECT config_json FROM runs WHERE run_id=?", (args.run,)
            ).fetchone()
        if row is None:
            raise ValueError("Unknown scrape run")
        config = json.loads(row[0])
        profile = ModelProfile(
            model=config[f"{args.kind}_model"],
            revision=config[f"{args.kind}_revision"],
            base_url="http://127.0.0.1:"
            + ("8001" if args.kind == "embedding" else "8002")
            + "/v1",
            runner="pooling",
            context_length=512 if args.kind == "embedding" else 256,
            server_args=[
                "--pooler-config",
                '{"pooling_type":"MEAN","use_activation":true}',
                "--gpu-memory-utilization",
                "0.15",
                "--enforce-eager",
            ],
        )
    if profile.engine != "vllm" or profile.engine_version != "0.28.0":
        raise ValueError(
            "This launcher uses the locked vLLM 0.28.0 runtime; launch other runtimes separately"
        )
    url = urlparse(profile.base_url)
    if url.hostname not in {"127.0.0.1", "localhost"} or url.scheme != "http":
        raise ValueError("The local launcher requires a loopback HTTP endpoint")
    reserved = {
        "--host",
        "--port",
        "--revision",
        "--tokenizer-revision",
        "--served-model-name",
        "--runner",
        "--max-model-len",
    }
    if any(arg.split("=", 1)[0] in reserved for arg in profile.server_args):
        raise ValueError(
            "Server arguments must not override profile identity or endpoint"
        )
    env = dict(os.environ)
    # FlashInfer JIT kernels need the toolkit compiler, not just the driver.
    toolkit = Path(env.get("CUDA_HOME", "/usr/local/cuda"))
    if (toolkit / "bin" / "nvcc").is_file():
        env["CUDA_HOME"] = str(toolkit)
        env["PATH"] = str(toolkit / "bin") + os.pathsep + env.get("PATH", "")
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
        profile.model,
        "--revision",
        profile.revision,
        "--tokenizer-revision",
        profile.revision,
        "--served-model-name",
        profile.served_model,
        "--runner",
        profile.runner,
        "--host",
        "127.0.0.1",
        "--port",
        str(url.port or 80),
        "--max-model-len",
        str(profile.context_length),
        *profile.server_args,
    ]
    if args.dry_run:
        import shlex

        print(shlex.join(command))
        return
    subprocess.run(command, env=env, check=True)


if __name__ == "__main__":
    main()
