"""Build a factor inventory from a unified GraphText JSONL file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lemon_factor.factors.inventory import build_inventory_from_jsonl, summarize_inventory


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", help="Input unified GraphText JSONL file")
    parser.add_argument("--out", default="data/interim/webnlg_factor_inventory.json")
    parser.add_argument("--summary", default="data/reports/webnlg_factor_inventory_summary.json")
    parser.add_argument("--max-contexts", type=int, default=5)
    parser.add_argument("--top-k", type=int, default=20)
    args = parser.parse_args()

    inventory = build_inventory_from_jsonl(args.jsonl, max_contexts_per_item=args.max_contexts)
    inventory.to_json_file(args.out)

    summary = summarize_inventory(inventory, top_k=args.top_k)
    summary_path = Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"inventory": args.out, "summary": args.summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
