"""Run once using: uv run python scripts/backfill_legacy.py --help."""

import argparse
import json

from uw_coursemap.legacy import git, import_revision
from uw_coursemap.store import Store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository", required=True, help="Initialized legacy data Git checkout"
    )
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument(
        "--all", action="store_true", help="Import every reachable commit, oldest first"
    )
    args = parser.parse_args()
    revisions = (
        git(args.repository, "rev-list", "--reverse", args.revision)
        .decode()
        .splitlines()
        if args.all
        else [args.revision]
    )
    store = Store(args.workspace)
    try:
        with store.lock():
            for revision in revisions:
                print(
                    json.dumps(import_revision(store, args.repository, revision)),
                    flush=True,
                )
    finally:
        store.close()


if __name__ == "__main__":
    main()
