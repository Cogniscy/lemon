"""Validate fixed predicate-factor inventories and report predicate coverage.

The inventory format reuses :class:`PredicateDecompositionSet`: a controlled
factor vocabulary plus weighted predicate decompositions. This validator is
offline and deterministic; it does not call an LLM or any external service.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from lemon_factor.datasets.unified_io import read_jsonl
from lemon_factor.factors.decomposition import PredicateDecompositionSet


def _collect_data_predicates(paths: list[str | Path]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for path in paths:
        for example in read_jsonl(path):
            for edge in example.edges:
                counts[edge.pred] += 1
    return counts


def _weight_sums(inventory: PredicateDecompositionSet) -> dict[str, float]:
    return {
        predicate: round(sum(component.weight for component in decomposition.components), 6)
        for predicate, decomposition in inventory.decompositions.items()
    }


def _factor_role_counts(inventory: PredicateDecompositionSet) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for decomposition in inventory.decompositions.values():
        for component in decomposition.components:
            counts[component.role] += 1
    return dict(sorted(counts.items()))


def validate_inventory(
    inventory_path: str | Path,
    *,
    data_paths: list[str | Path] | None = None,
    min_coverage: float = 0.0,
) -> dict[str, Any]:
    """Validate an inventory and return a JSON-serializable report."""

    inventory_path = Path(inventory_path)
    inventory = PredicateDecompositionSet.from_json_file(inventory_path)
    factor_ids = {factor.id for factor in inventory.factors}
    referenced_factors = {
        component.factor
        for decomposition in inventory.decompositions.values()
        for component in decomposition.components
    }
    unused_factors = sorted(factor_ids - referenced_factors)
    weight_sums = _weight_sums(inventory)

    data_predicates: Counter[str] = Counter()
    covered_predicates: list[str] = []
    missing_predicates: list[str] = []
    coverage = None
    if data_paths:
        data_predicates = _collect_data_predicates(data_paths)
        covered_predicates = sorted(set(data_predicates) & set(inventory.decompositions))
        missing_predicates = sorted(set(data_predicates) - set(inventory.decompositions))
        coverage = len(covered_predicates) / len(data_predicates) if data_predicates else 1.0
        if coverage < min_coverage:
            raise ValueError(
                f"Predicate coverage {coverage:.3f} is below requested minimum {min_coverage:.3f}"
            )

    return {
        "status": "passed",
        "inventory": str(inventory_path),
        "schema_version": inventory.schema_version,
        "metadata": inventory.metadata,
        "factor_count": len(inventory.factors),
        "predicate_count": len(inventory.decompositions),
        "referenced_factor_count": len(referenced_factors),
        "unused_factor_count": len(unused_factors),
        "unused_factors": unused_factors,
        "role_component_counts": _factor_role_counts(inventory),
        "weight_sums_valid": all(abs(value - 1.0) <= 1e-6 for value in weight_sums.values()),
        "data_predicate_count": len(data_predicates),
        "data_edge_count": sum(data_predicates.values()),
        "covered_predicate_count": len(covered_predicates),
        "missing_predicate_count": len(missing_predicates),
        "predicate_coverage": coverage,
        "missing_predicates": missing_predicates[:50],
    }


def report_to_markdown(report: dict[str, Any]) -> str:
    """Render one inventory report as a compact Markdown table."""

    coverage = report.get("predicate_coverage")
    coverage_text = "-" if coverage is None else f"{coverage:.3f}"
    metadata = report.get("metadata") or {}
    dataset = metadata.get("dataset") or metadata.get("domain") or "unknown"
    rows = [
        "| Field | Value |",
        "|---|---:|",
        f"| Dataset | {dataset} |",
        f"| Schema version | {report.get('schema_version', '-')} |",
        f"| Factors | {report.get('factor_count', 0)} |",
        f"| Predicate decompositions | {report.get('predicate_count', 0)} |",
        f"| Referenced factors | {report.get('referenced_factor_count', 0)} |",
        f"| Data predicates | {report.get('data_predicate_count', 0)} |",
        f"| Covered data predicates | {report.get('covered_predicate_count', 0)} |",
        f"| Predicate coverage | {coverage_text} |",
        f"| Missing data predicates | {report.get('missing_predicate_count', 0)} |",
    ]
    return "\n".join(rows) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", required=True, help="Predicate-factor inventory JSON")
    parser.add_argument(
        "--data",
        action="append",
        default=[],
        help="Optional GraphText JSONL file. Repeat for multiple splits.",
    )
    parser.add_argument("--out", default="reports/factor_inventory_report.json")
    parser.add_argument("--table-out", default=None, help="Optional Markdown report path")
    parser.add_argument("--min-coverage", type=float, default=0.0)
    args = parser.parse_args()

    report = validate_inventory(args.inventory, data_paths=args.data, min_coverage=args.min_coverage)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.table_out:
        table_path = Path(args.table_out)
        table_path.parent.mkdir(parents=True, exist_ok=True)
        table_path.write_text(report_to_markdown(report), encoding="utf-8")

    print(json.dumps({"out": str(out_path), "status": report["status"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
