"""Small helpers for exporting LEMON-Factor coverage reports as markdown."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def write_coverage_table(report_path: str | Path, out_path: str | Path) -> None:
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    lines = [
        "| Method / diagnostic | Score |",
        "|---|---:|",
        f"| Exact label coverage | {report['exact_label_coverage']:.4f} |",
        f"| Predicate cue coverage | {report['predicate_cue_coverage']:.4f} |",
        f"| LEMON-Factor coverage | {report['lemon_factor_coverage']:.4f} |",
        f"| Missing decomposition rate | {report['missing_decomposition_rate']:.4f} |",
    ]
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    write_coverage_table(args.report, args.out)
    print(args.out)


if __name__ == "__main__":  # pragma: no cover
    main()
