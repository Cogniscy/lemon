"""Read/write helpers for unified GraphText JSONL files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from lemon_factor.schema.graphtext import GraphTextExample


def read_jsonl(path: str | Path) -> list[GraphTextExample]:
    examples: list[GraphTextExample] = []
    with Path(path).open("r", encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                examples.append(GraphTextExample.model_validate_json(stripped))
            except Exception as exc:  # pragma: no cover - keeps line context
                raise ValueError(f"Invalid GraphText JSONL at {path}:{line_no}") from exc
    return examples


def write_jsonl(path: str | Path, examples: Iterable[GraphTextExample]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for example in examples:
            stream.write(json.dumps(example.model_dump(mode="json"), ensure_ascii=False) + "\n")
