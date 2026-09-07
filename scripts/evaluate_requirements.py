"""Run the small manually checked requirements benchmark against a pinned server."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

from uw_coursemap.jobs import WORKER_VERSION, check_server, generate
from uw_coursemap.models import digest
from uw_coursemap.profiles import load_profile
from uw_coursemap.requirements_eval import expression, matches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models-config", required=True)
    parser.add_argument("--profile", default="requirements")
    parser.add_argument(
        "--task", type=Path, default=Path("inference/tasks/requirements.json")
    )
    parser.add_argument(
        "--cases", type=Path, default=Path("inference/evals/requirements.json")
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    profile = load_profile(args.models_config, args.profile).model_dump()
    task = json.loads(args.task.read_text())
    fixtures = json.loads(args.cases.read_text())
    check_server(profile)

    def run(case):
        try:
            value, usage = generate(profile, task, case["payload"])
            result = {
                "id": case["id"],
                "valid": True,
                "match": matches(case, value),
                "expression": expression(value),
                "output": value,
                "usage": usage,
            }
        except Exception as exc:
            result = {
                "id": case["id"],
                "valid": False,
                "match": False,
                "error": str(exc),
                "error_type": type(exc).__name__,
            }
        print(json.dumps({k: result[k] for k in ["id", "valid", "match"]}), flush=True)
        return result

    with ThreadPoolExecutor(max_workers=profile["concurrency"]) as pool:
        results = list(pool.map(run, fixtures["cases"]))
    report = {
        "worker_version": WORKER_VERSION,
        "profile": profile,
        "task_hash": digest(task),
        "fixtures_hash": digest(fixtures),
        "task": task,
        "fixtures": fixtures,
        "results": results,
        "valid": sum(r["valid"] for r in results),
        "matched": sum(r["match"] for r in results),
        "total": len(results),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: report[k] for k in ["valid", "matched", "total"]}), flush=True)
    return 0 if report["matched"] == report["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
