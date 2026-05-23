"""Quality gates for biomedical GraphText conversion outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from lemon_factor.datasets.biomedical_common import now_utc_iso
from lemon_factor.datasets.unified_io import read_jsonl
from lemon_factor.schema.graphtext import GraphTextExample


def summarize_quality(examples: list[GraphTextExample]) -> dict[str, Any]:
    """Return compact quality statistics for converted biomedical examples."""

    examples_with_text = sum(1 for ex in examples if ex.text.strip())
    examples_with_edges = sum(1 for ex in examples if ex.edges)
    examples_with_nodes = sum(1 for ex in examples if ex.nodes)
    edges_total = sum(len(ex.edges) for ex in examples)
    predicates = sorted({edge.pred for ex in examples for edge in ex.edges})
    text_chars_avg = sum(len(ex.text) for ex in examples) / len(examples) if examples else 0.0
    return {
        "examples": len(examples),
        "examples_with_text": examples_with_text,
        "examples_with_nodes": examples_with_nodes,
        "examples_with_edges": examples_with_edges,
        "edges_total": edges_total,
        "predicate_count": len(predicates),
        "predicates": predicates,
        "text_chars_avg": text_chars_avg,
        "nonempty_text_ratio": examples_with_text / len(examples) if examples else 0.0,
        "nonempty_edge_ratio": examples_with_edges / len(examples) if examples else 0.0,
    }


def validate_quality(
    stats: dict[str, Any],
    *,
    min_examples: int = 1,
    min_edges: int = 1,
    min_predicates: int = 1,
    require_text: bool = True,
) -> list[str]:
    """Return validation errors for one biomedical conversion output."""

    errors: list[str] = []
    if int(stats.get("examples", 0)) < min_examples:
        errors.append(f"expected at least {min_examples} examples, found {stats.get('examples', 0)}")
    if int(stats.get("edges_total", 0)) < min_edges:
        errors.append(f"expected at least {min_edges} edges, found {stats.get('edges_total', 0)}")
    if int(stats.get("predicate_count", 0)) < min_predicates:
        errors.append(f"expected at least {min_predicates} predicates, found {stats.get('predicate_count', 0)}")
    if require_text and float(stats.get("nonempty_text_ratio", 0.0)) < 1.0:
        errors.append(
            "expected every converted example to have non-empty text, "
            f"found ratio {float(stats.get('nonempty_text_ratio', 0.0)):.3f}"
        )
    return errors


def summarize_path(path: str | Path) -> dict[str, Any]:
    examples = read_jsonl(path)
    stats = summarize_quality(examples)
    stats["path"] = str(path)
    stats["dataset"] = examples[0].dataset if examples else "unknown"
    stats["split"] = examples[0].split.value if examples else "unknown"
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Converted biomedical GraphText JSONL files")
    parser.add_argument("--out", default="data/biomedical/reports/biomedical_quality_check.json")
    parser.add_argument("--min-examples", type=int, default=1)
    parser.add_argument("--min-edges", type=int, default=1)
    parser.add_argument("--min-predicates", type=int, default=1)
    parser.add_argument("--allow-empty-text", action="store_true")
    args = parser.parse_args()

    payload: dict[str, Any] = {"generated_at": now_utc_iso(), "paths": {}}
    failed = False
    for path in args.paths:
        stats = summarize_path(path)
        errors = validate_quality(
            stats,
            min_examples=args.min_examples,
            min_edges=args.min_edges,
            min_predicates=args.min_predicates,
            require_text=not args.allow_empty_text,
        )
        stats["errors"] = errors
        stats["status"] = "failed" if errors else "passed"
        failed = failed or bool(errors)
        payload["paths"][str(path)] = stats

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(out), "status": "failed" if failed else "passed"}, ensure_ascii=False, indent=2))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
