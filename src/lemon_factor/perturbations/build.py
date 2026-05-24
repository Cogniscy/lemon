"""Build controlled perturbation JSONL files for LEMON-Factor experiments."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from lemon_factor.datasets.unified_io import read_jsonl
from lemon_factor.perturbations.rules import build_perturbed_record
from lemon_factor.perturbations.schema import PerturbationVariant, PerturbedGraphTextRecord

DEFAULT_VARIANTS: list[PerturbationVariant] = [
    "node_deletion",
    "edge_deletion",
    "argument_swap",
    "polarity_flip",
    "relation_blur",
]


def _default_report_path(out: Path) -> Path:
    if out.suffix == ".jsonl":
        return out.with_name(f"{out.stem}_report.json")
    return out.with_suffix(out.suffix + ".report.json")


def _default_table_path(out: Path) -> Path:
    if out.suffix == ".jsonl":
        return out.with_name(f"{out.stem}_report.md")
    return out.with_suffix(out.suffix + ".report.md")


def write_jsonl_dicts(path: str | Path, records: Iterable[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for record in records:
            # Validate before writing so downstream modules get stable records.
            PerturbedGraphTextRecord.model_validate(record)
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")


def summarize_records(records: list[dict], *, input_path: str | Path, out_path: str | Path, examples_read: int, examples_used: int) -> dict:
    variant_counts = Counter(record["variant"] for record in records)
    changed_counts: Counter[str] = Counter()
    target_groups: dict[str, set[str]] = defaultdict(set)
    severity_by_variant: dict[str, str] = {}
    for record in records:
        changed = any(operation.get("changed") for operation in record.get("operations", []))
        if changed:
            changed_counts[record["variant"]] += 1
        target_groups[record["variant"]].update(record.get("target_factor_groups", []))
        severity_by_variant[record["variant"]] = record.get("expected_damage", {}).get("severity", "")
    by_variant = []
    for variant in sorted(variant_counts):
        count = variant_counts[variant]
        changed = changed_counts[variant]
        by_variant.append(
            {
                "variant": variant,
                "records": count,
                "changed": changed,
                "changed_ratio": round(changed / count, 4) if count else 0.0,
                "severity": severity_by_variant.get(variant, ""),
                "target_factor_groups": sorted(target_groups[variant]),
            }
        )
    return {
        "status": "passed",
        "input": str(input_path),
        "out": str(out_path),
        "examples_read": examples_read,
        "examples_used": examples_used,
        "records_written": len(records),
        "variants": by_variant,
    }


def report_to_markdown(report: dict) -> str:
    lines = [
        "| Variant | Records | Changed | Changed ratio | Severity | Target factor groups |",
        "|---|---:|---:|---:|---|---|",
    ]
    for item in report.get("variants", []):
        groups = ", ".join(item.get("target_factor_groups", []))
        lines.append(
            f"| {item['variant']} | {item['records']} | {item['changed']} | "
            f"{item['changed_ratio']:.3f} | {item['severity']} | {groups} |"
        )
    return "\n".join(lines) + "\n"


def build_perturbations(
    input_path: str | Path,
    out_path: str | Path,
    *,
    variants: list[PerturbationVariant] | None = None,
    limit: int | None = None,
    report_out: str | Path | None = None,
    table_out: str | Path | None = None,
) -> dict:
    variants = variants or DEFAULT_VARIANTS
    examples = read_jsonl(input_path)
    selected = examples[:limit] if limit is not None else examples
    records: list[dict] = []
    for example in selected:
        if not example.edges:
            continue
        for variant in variants:
            records.append(build_perturbed_record(example, variant))
    write_jsonl_dicts(out_path, records)

    report = summarize_records(
        records,
        input_path=input_path,
        out_path=out_path,
        examples_read=len(examples),
        examples_used=len(selected),
    )
    report_path = Path(report_out) if report_out else _default_report_path(Path(out_path))
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    table_path = Path(table_out) if table_out else _default_table_path(Path(out_path))
    table_path.parent.mkdir(parents=True, exist_ok=True)
    table_path.write_text(report_to_markdown(report), encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input GraphText JSONL file")
    parser.add_argument("--out", required=True, help="Output perturbation JSONL file")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of input examples to use")
    parser.add_argument("--variant", choices=DEFAULT_VARIANTS, action="append", help="Variant to generate; may be repeated")
    parser.add_argument("--report-out", default=None, help="Optional JSON report path")
    parser.add_argument("--table-out", default=None, help="Optional Markdown report path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_perturbations(
        args.input,
        args.out,
        variants=args.variant or DEFAULT_VARIANTS,
        limit=args.limit,
        report_out=args.report_out,
        table_out=args.table_out,
    )
    print(json.dumps({"out": args.out, "status": report["status"], "records": report["records_written"]}, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
