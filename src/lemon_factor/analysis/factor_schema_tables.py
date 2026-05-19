"""Export markdown tables for seed factor schema and predicate decompositions."""

from __future__ import annotations

import argparse
from pathlib import Path

from lemon_factor.factors.decomposition import PredicateDecompositionSet, read_factor_schema


def _escape(value: object) -> str:
    return str(value).replace("\n", " ").replace("|", "\\|")


def _format_confidence(value: float | None) -> str:
    return "" if value is None else f"{value:.2f}"


def factor_schema_to_markdown(schema_path: str | Path, *, top_k: int | None = None) -> str:
    factors = read_factor_schema(schema_path)
    if top_k is not None:
        factors = factors[:top_k]
    rows = [
        "| Factor | Level | Allowed roles | Parents | Description |",
        "|---|---|---|---|---|",
    ]
    for factor in factors:
        rows.append(
            f"| {_escape(factor.id)} | {_escape(factor.level)} | "
            f"{_escape(', '.join(factor.allowed_roles))} | "
            f"{_escape(', '.join(factor.parents))} | {_escape(factor.description)} |"
        )
    return "\n".join(rows) + "\n"


def decompositions_to_markdown(
    decompositions_path: str | Path,
    *,
    top_k: int = 30,
) -> str:
    decomposition_set = PredicateDecompositionSet.from_json_file(decompositions_path)
    rows = [
        "| Predicate | Components | Confidence | Evidence categories |",
        "|---|---|---:|---|",
    ]
    items = sorted(
        decomposition_set.decompositions.values(),
        key=lambda item: (-int(item.evidence.get("count", 0)), item.predicate),
    )[:top_k]
    for decomposition in items:
        components = "; ".join(
            f"{component.factor}/{component.role}/{component.weight:.2f}"
            for component in decomposition.components
        )
        categories = decomposition.evidence.get("categories", {})
        category_text = ", ".join(
            f"{category}:{count}"
            for category, count in sorted(categories.items(), key=lambda pair: (-pair[1], pair[0]))
        )
        rows.append(
            f"| {_escape(decomposition.predicate)} | {_escape(components)} | "
            f"{_format_confidence(decomposition.confidence)} | {_escape(category_text)} |"
        )
    return "\n".join(rows) + "\n"


def write_text(path: str | Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", required=True, help="Input factor schema JSON")
    parser.add_argument("--decompositions", required=True, help="Input decomposition set JSON")
    parser.add_argument("--schema-out", default="paper/tables/table_factor_schema_seed.md")
    parser.add_argument("--decompositions-out", default="paper/tables/table_predicate_decompositions_seed.md")
    parser.add_argument("--top-k", type=int, default=30)
    args = parser.parse_args()

    write_text(args.schema_out, factor_schema_to_markdown(args.schema))
    write_text(
        args.decompositions_out,
        decompositions_to_markdown(args.decompositions, top_k=args.top_k),
    )
    print(str(args.schema_out))
    print(str(args.decompositions_out))


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
