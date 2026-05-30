"""Validate the local score against the MINE-1 aggregation formula.

The official MINE-1 score is the mean percentage of binary fact-recoverability
judgments.  This helper is intentionally simple: it verifies that a list of
0/1 decisions aggregates to the expected score.  It is useful for checking our
implementation against public KGGen/MINE outputs when a small external run is
available.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import mine1_score


def load_decisions(path: str) -> list[bool]:
    payload = json.loads(Path(path).read_text(encoding="utf8"))
    if isinstance(payload, list):
        return [bool(row.get("score", row.get("recoverable", row))) if isinstance(row, dict) else bool(row) for row in payload]
    if isinstance(payload, dict) and "decisions" in payload:
        return [bool(row.get("score", row.get("recoverable", row))) if isinstance(row, dict) else bool(row) for row in payload["decisions"]]
    raise ValueError("Expected a JSON list or an object with a 'decisions' list")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decisions", required=True)
    parser.add_argument("--expected", type=float, required=True)
    parser.add_argument("--tolerance", type=float, default=1e-9)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    decisions = load_decisions(args.decisions)
    score = mine1_score(decisions)
    passed = abs(score - args.expected) <= args.tolerance
    report = {"status": "passed" if passed else "failed", "items": len(decisions), "score": score, "expected": args.expected}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf8")
    print(json.dumps(report, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
