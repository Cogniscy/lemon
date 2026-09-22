"""Small offline entry points; research modules retain their own CLIs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from lemon_factor.demo import build_demo, render_demo, reproduce_demo


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m lemon_factor")
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="Score packaged examples without network access")
    demo.add_argument("--format", choices=("text", "json"), default="text")
    reproduce = commands.add_parser("reproduce-demo", help="Write scores, summary and provenance")
    reproduce.add_argument("--out", type=Path, required=True)
    reproduce.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            report = build_demo()
            print(json.dumps(report, ensure_ascii=False, indent=2) if args.format == "json"
                  else render_demo(report))
        else:
            reproduce_demo(args.out, overwrite=args.overwrite)
            print(f"Wrote scores.json, summary.md and manifest.json to {args.out}")
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Error: {exc}\n")
    return 0
