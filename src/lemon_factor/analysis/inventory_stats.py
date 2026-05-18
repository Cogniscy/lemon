"""Export compact markdown tables from a factor inventory."""

from __future__ import annotations

import argparse
from pathlib import Path

from lemon_factor.factors.inventory import FactorInventory


def _escape(value: object) -> str:
    text = str(value).replace("\n", " ")
    return text.replace("|", "\\|")


def inventory_to_markdown_table(inventory: FactorInventory, *, top_k: int = 20) -> str:
    """Render top predicate inventory rows as a markdown table."""

    rows = [
        "| Predicate | Count | Categories | Candidate factors | Example |",
        "|---|---:|---|---|---|",
    ]
    top_predicates = sorted(
        inventory.predicates.values(), key=lambda item: (-item.count, item.predicate)
    )[:top_k]
    for item in top_predicates:
        categories = ", ".join(
            f"{category}:{count}"
            for category, count in sorted(item.categories.items(), key=lambda pair: (-pair[1], pair[0]))
        )
        factors = ", ".join(item.candidate_factors)
        example = ""
        if item.examples:
            first = item.examples[0]
            example = f"{first.get('subj', '')} — {item.predicate} — {first.get('obj', '')}"
        rows.append(
            f"| {_escape(item.predicate)} | {item.count} | {_escape(categories)} | "
            f"{_escape(factors)} | {_escape(example)} |"
        )
    return "\n".join(rows) + "\n"


def write_inventory_table(inventory_path: str | Path, out_path: str | Path, *, top_k: int = 20) -> None:
    inventory = FactorInventory.from_json_file(inventory_path)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(inventory_to_markdown_table(inventory, top_k=top_k), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", help="Input factor inventory JSON file")
    parser.add_argument("--out", default="paper/tables/table_webnlg_inventory.md")
    parser.add_argument("--top-k", type=int, default=20)
    args = parser.parse_args()
    write_inventory_table(args.inventory, args.out, top_k=args.top_k)
    print(str(args.out))


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
