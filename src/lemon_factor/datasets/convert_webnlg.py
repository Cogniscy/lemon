"""Convert WebNLG parquet records to unified GraphText JSONL."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from lemon_factor.datasets.normalization import parse_webnlg_triple, stable_id
from lemon_factor.datasets.unified_io import write_jsonl
from lemon_factor.datasets.webnlg_loader import get_split, load_webnlg_parquet, take_rows
from lemon_factor.schema.graphtext import Edge, Fact, GraphTextExample, Node, Split


def _record_id(record: dict[str, Any], split: str, index: int) -> str:
    return str(record.get("gem_id") or record.get("webnlg_id") or f"webnlg_{split}_{index}")


def webnlg_record_to_graphtext(
    record: dict[str, Any],
    *,
    split: str,
    index: int = 0,
    language: str = "en",
) -> GraphTextExample:
    """Convert one WebNLG parquet row to a validated GraphTextExample."""

    raw_triples = record.get("input") or []
    if isinstance(raw_triples, str):
        raw_triples = [raw_triples]
    if not isinstance(raw_triples, list):
        raise TypeError(f"WebNLG input must be a list or string, got {type(raw_triples)!r}")

    node_by_label: dict[str, Node] = {}
    edges: list[Edge] = []
    facts: list[Fact] = []

    for triple_index, raw_triple in enumerate(raw_triples):
        parsed = parse_webnlg_triple(str(raw_triple))
        subj_id = stable_id("n", parsed.subj)
        obj_id = stable_id("n", parsed.obj)
        node_by_label.setdefault(subj_id, Node(id=subj_id, label=parsed.subj))
        node_by_label.setdefault(obj_id, Node(id=obj_id, label=parsed.obj))

        edge = Edge(
            subj=subj_id,
            pred=parsed.pred,
            obj=obj_id,
            evidence=record.get("target") or None,
            metadata={"raw_triple": parsed.raw, "triple_index": triple_index},
        )
        edges.append(edge)
        facts.append(
            Fact(
                id=f"f{triple_index}",
                text=f"{parsed.subj} {parsed.pred} {parsed.obj}",
                source="gold",
                edge_refs=[triple_index],
                metadata={
                    "source": "webnlg_triple",
                    "subj": parsed.subj,
                    "pred": parsed.pred,
                    "obj": parsed.obj,
                    "raw_triple": parsed.raw,
                },
            )
        )

    mapped_split = Split.dev if split == "validation" else Split(split)
    return GraphTextExample(
        id=_record_id(record, split, index),
        dataset="webnlg",
        split=mapped_split,
        text=str(record.get("target") or ""),
        language=language,
        nodes=list(node_by_label.values()),
        edges=edges,
        facts=facts,
        metadata={
            "gem_id": record.get("gem_id"),
            "gem_parent_id": record.get("gem_parent_id"),
            "category": record.get("category"),
            "webnlg_id": record.get("webnlg_id"),
            "references": record.get("references") or [],
        },
    )


def convert_records(
    records: Iterable[dict[str, Any]],
    *,
    split: str,
    language: str = "en",
) -> list[GraphTextExample]:
    """Convert multiple WebNLG rows to GraphText examples."""

    return [
        webnlg_record_to_graphtext(record, split=split, index=index, language=language)
        for index, record in enumerate(records)
    ]


def convert_webnlg_dataset(
    *,
    language: str,
    n_train: int | None,
    n_dev: int | None,
    out_dir: str | Path,
) -> dict[str, Path]:
    """Load WebNLG parquet data and write train/dev GraphText JSONL files."""

    dataset = load_webnlg_parquet(language)
    out_dir = Path(out_dir)
    train_examples = convert_records(
        take_rows(get_split(dataset, "train"), n_train), split="train", language=language
    )
    dev_examples = convert_records(
        take_rows(get_split(dataset, "validation"), n_dev), split="validation", language=language
    )

    train_path = out_dir / "webnlg_train.jsonl"
    dev_path = out_dir / "webnlg_dev.jsonl"
    write_jsonl(train_path, train_examples)
    write_jsonl(dev_path, dev_examples)
    return {"train": train_path, "dev": dev_path}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", default="en", help="WebNLG parquet language/config, e.g. en or ru")
    parser.add_argument("--n-train", type=int, default=100, help="Number of train rows to export")
    parser.add_argument("--n-dev", type=int, default=50, help="Number of validation rows to export")
    parser.add_argument("--out-dir", default="data/processed", help="Output directory")
    args = parser.parse_args()

    paths = convert_webnlg_dataset(
        language=args.language,
        n_train=args.n_train,
        n_dev=args.n_dev,
        out_dir=args.out_dir,
    )
    print(json.dumps({key: str(value) for key, value in paths.items()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
