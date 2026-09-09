"""Website build commands, independent of scraping and inference."""

import argparse
import json
from pathlib import Path
import sys


def check_assets(root: Path):
    files = [
        p
        for p in root.rglob("*")
        if p.is_file() and "_worker.js" not in p.relative_to(root).parts
    ]
    if not files:
        raise ValueError("No built assets found")
    largest = max(files, key=lambda p: p.stat().st_size)
    # Keep 10,000 files of headroom below Workers Paid's 100,000-asset limit.
    if len(files) > 90000:
        raise ValueError(f"Asset count {len(files)} exceeds 90,000")
    if largest.stat().st_size > 20 * 1024 * 1024:
        raise ValueError(f"Asset exceeds 20 MiB: {largest}")
    report = {
        "files": len(files),
        "bytes": sum(p.stat().st_size for p in files),
        "largest": str(largest),
        "largest_bytes": largest.stat().st_size,
    }
    print(json.dumps(report, indent=2))
    return report


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "import":
        from .importer import main as import_main

        del sys.argv[1]
        import_main()
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("command", choices=["assets-check"])
        parser.add_argument("--root", type=Path, default=Path(".svelte-kit/cloudflare"))
        args = parser.parse_args()
        check_assets(args.root)


if __name__ == "__main__":
    main()
