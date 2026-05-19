"""Expand predicate decompositions for predicates missed by coverage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from lemon_factor.coverage.missing_analysis import MissingPredicateReport
from lemon_factor.factors.candidates import candidate_factors_from_predicate
from lemon_factor.factors.decomposition import PredicateDecomposition, PredicateDecompositionSet
from lemon_factor.factors.inventory import FactorInventory, PredicateInventoryItem
from lemon_factor.factors.seed_builder import decompose_predicate


def _missing_item_to_inventory_item(item: Any) -> PredicateInventoryItem:
    return PredicateInventoryItem(
        predicate=item.predicate,
        count=item.count,
        categories=item.categories,
        candidate_factors=candidate_factors_from_predicate(item.predicate),
        examples=item.examples,
    )


def _as_expanded(decomposition: PredicateDecomposition, *, missing_count: int) -> PredicateDecomposition:
    source = "fallback_rule" if decomposition.source == "fallback" else "expansion_rule"
    confidence = decomposition.confidence
    if source == "fallback_rule" and confidence is not None:
        confidence = min(confidence, 0.45)
    elif confidence is not None:
        confidence = min(confidence, 0.68)
    evidence = dict(decomposition.evidence)
    evidence.update({"expanded_from_missing_report": True, "missing_edge_count": missing_count})
    return decomposition.model_copy(update={"source": source, "confidence": confidence, "evidence": evidence})


def expand_decomposition_set(
    base: PredicateDecompositionSet,
    missing_report: MissingPredicateReport,
    *,
    inventory: FactorInventory | None = None,
    max_new_predicates: int | None = None,
) -> PredicateDecompositionSet:
    """Add deterministic decompositions for missing predicates."""

    decompositions = dict(base.decompositions)
    added: list[str] = []
    skipped_existing: list[str] = []
    missing_items = list(missing_report.predicates.values())
    if max_new_predicates is not None:
        missing_items = missing_items[:max_new_predicates]

    for missing_item in missing_items:
        predicate = missing_item.predicate
        if predicate in decompositions:
            skipped_existing.append(predicate)
            continue
        inventory_item = inventory.predicates.get(predicate) if inventory else None
        item = inventory_item or _missing_item_to_inventory_item(missing_item)
        decomposition = _as_expanded(decompose_predicate(item), missing_count=missing_item.count)
        decompositions[predicate] = decomposition
        added.append(predicate)

    metadata = dict(base.metadata)
    metadata.update(
        {
            "expanded": True,
            "expansion_source": "coverage_missing_predicates",
            "added_predicate_count": len(added),
            "added_predicates": added,
            "skipped_existing_predicates": skipped_existing,
            "missing_report_predicate_count": missing_report.predicate_count,
        }
    )
    return PredicateDecompositionSet(
        schema_version=base.schema_version,
        factors=base.factors,
        decompositions=decompositions,
        metadata=metadata,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--missing", required=True, help="Missing-predicate JSON report")
    parser.add_argument("--base", required=True, help="Base PredicateDecompositionSet JSON")
    parser.add_argument("--inventory", default=None, help="Optional factor inventory JSON")
    parser.add_argument("--out", required=True, help="Expanded PredicateDecompositionSet JSON")
    parser.add_argument("--max-new-predicates", type=int, default=None)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    base = PredicateDecompositionSet.from_json_file(args.base)
    missing = MissingPredicateReport.from_json_file(args.missing)
    inventory = FactorInventory.from_json_file(args.inventory) if args.inventory else None
    expanded = expand_decomposition_set(
        base,
        missing,
        inventory=inventory,
        max_new_predicates=args.max_new_predicates,
    )
    expanded.to_json_file(args.out)
    print(
        json.dumps(
            {
                "out": args.out,
                "added_predicate_count": expanded.metadata.get("added_predicate_count", 0),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":  # pragma: no cover
    main()
