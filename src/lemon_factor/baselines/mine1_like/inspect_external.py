"""Inspect a local KGGen/MINE checkout and record a smoke-run plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

KEYWORDS = ("mine", "evaluation", "fact", "subgraph", "judge", "embedding")


def inspect(checkout: str, out: str) -> dict[str, Any]:
    root = Path(checkout)
    mine_dir = root / "experiments" / "MINE"
    files = []
    snippets = []
    if mine_dir.exists():
        for path in sorted(mine_dir.rglob("*")):
            if path.is_file():
                rel = path.relative_to(root).as_posix()
                files.append(rel)
                if path.suffix.lower() in {".md", ".py", ".txt", ".yaml", ".yml"}:
                    try:
                        text = path.read_text(encoding="utf8", errors="ignore")
                    except OSError:
                        text = ""
                    lower = text.lower()
                    if any(key in lower for key in KEYWORDS):
                        snippets.append({"file": rel, "preview": "\n".join(text.splitlines()[:40])})
    report = {
        "status": "passed" if mine_dir.exists() else "missing_checkout",
        "checkout": str(root),
        "mine_dir": str(mine_dir),
        "mine_dir_exists": mine_dir.exists(),
        "files": files,
        "snippets": snippets[:8],
        "recommended_next_step": "Run the official KGGen/MINE scripts on a 3--5 example subset if dependencies and API keys are available.",
    }
    target = Path(out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf8")
    md = target.with_suffix(".md")
    lines = ["# KGGen/MINE external inspection", "", f"Status: `{report['status']}`", f"Checkout: `{root}`", "", "## MINE files"]
    lines += [f"- `{f}`" for f in files[:80]] or ["- none"]
    lines += ["", "## Inspection notes", report["recommended_next_step"]]
    md.write_text("\n".join(lines) + "\n", encoding="utf8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", default="external/kg-gen")
    parser.add_argument("--out", default="reports/mine_external_inspection.json")
    args = parser.parse_args()
    report = inspect(args.checkout, args.out)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
