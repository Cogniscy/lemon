"""Export seed predicate decompositions to a CSV expert-review template."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from lemon_factor.factors.decomposition import PredicateDecompositionSet

REVIEW_COLUMNS = [
    "predicate",
    "count",
    "categories",
    "candidate_factors",
    "proposed_components",
    "proposed_weights",
    "confidence",
    "expert_label",
    "missing_factor",
    "wrong_factor",
    "weight_comment",
    "notes",
]


def _components_text(decomposition) -> str:
    return "; ".join(
        f"{component.factor}:{component.role}:{component.weight:.2f}"
        for component in decomposition.components
    )


def _weights_text(decomposition) -> str:
    return "; ".join(f"{component.factor}={component.weight:.2f}" for component in decomposition.components)


def decomposition_review_rows(decomposition_set: PredicateDecompositionSet) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for predicate, decomposition in sorted(decomposition_set.decompositions.items()):
        evidence = decomposition.evidence
        rows.append(
            {
                "predicate": predicate,
                "count": str(evidence.get("count", "")),
                "categories": json.dumps(evidence.get("categories", {}), ensure_ascii=False),
                "candidate_factors": ", ".join(evidence.get("candidate_factors", [])),
                "proposed_components": _components_text(decomposition),
                "proposed_weights": _weights_text(decomposition),
                "confidence": f"{decomposition.confidence:.2f}",
                "expert_label": "",
                "missing_factor": "",
                "wrong_factor": "",
                "weight_comment": "",
                "notes": "",
            }
        )
    return rows


def write_review_csv(decompositions_path: str | Path, out_path: str | Path) -> None:
    decomposition_set = PredicateDecompositionSet.from_json_file(decompositions_path)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=REVIEW_COLUMNS)
        writer.writeheader()
        writer.writerows(decomposition_review_rows(decomposition_set))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decompositions", help="Input predicate decomposition JSON")
    parser.add_argument("--out", default="data/annotation/predicate_decomposition_review.csv")
    args = parser.parse_args()
    write_review_csv(args.decompositions, args.out)
    print(str(args.out))


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
