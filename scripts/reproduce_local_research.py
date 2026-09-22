"""Recompute deterministic experiments from explicitly supplied local reports.

This does not acquire datasets, run models, or reproduce human annotations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from importlib.metadata import version
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from lemon_factor.scoring.score_perturbations import score_file
from lemon_factor.scoring.ablate import ablate_reports
from lemon_factor.scoring.report_schema import normalize_scoring_report


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(root: Path, reports: list[Path], out: Path) -> dict:
    root = root.resolve()
    out.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "local-research-reproduction-v1",
        "scope": "Prepared-input deterministic scoring and ablation; no upstream acquisition, LLM or human reruns.",
        "python": platform.python_version(), "pydantic": version("pydantic"),
        "datasets": [],
    }
    regenerated = []
    for report_path in reports:
        original = normalize_scoring_report(json.loads(report_path.read_text(encoding="utf-8")))
        source = (root / original["input"]).resolve()
        inventory = (root / original["inventory"]).resolve()
        dataset = original["dataset"]
        # Use the recorded sample size, not the size of a potentially expanded corpus.
        current = score_file(source, inventory, dataset=dataset, limit=original["record_count"])
        if current["rows"] != original["rows"] or current["summary"] != original["summary"]:
            raise ValueError(f"Recomputed scores differ from historical report: {report_path}")
        target = out / f"scoring_{dataset}.json"
        with target.open("x", encoding="utf-8") as stream:
            json.dump(current, stream, indent=2, ensure_ascii=False)
        regenerated.append(target)
        manifest["datasets"].append({
            "dataset": dataset, "records": current["record_count"],
            "input": original["input"], "input_sha256": digest(source),
            "inventory": original["inventory"], "inventory_sha256": digest(inventory),
            "historical_report": str(report_path.relative_to(root)),
            "historical_report_sha256": digest(report_path),
            "output": target.name, "output_sha256": digest(target),
            "historical_rows_and_summary_equal": True,
        })
    ablation = ablate_reports(regenerated)
    with (out / "ablation_summary.json").open("x", encoding="utf-8") as stream:
        json.dump(ablation, stream, ensure_ascii=False, indent=2)
    manifest["ablation_sha256"] = digest(out / "ablation_summary.json")
    with (out / "manifest.json").open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--reports", nargs="+", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        parser.error("--out must be an empty or new directory; existing outputs are preserved")
    try:
        root = args.root.resolve()
        result = run(root, [root / p for p in args.reports], args.out)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"Reproduction failed: {exc}\n")
    print(json.dumps({"datasets": len(result["datasets"]),
                      "records": sum(d["records"] for d in result["datasets"]),
                      "historical_scores_equal": True, "out": str(args.out)}, indent=2))


if __name__ == "__main__":
    main()
