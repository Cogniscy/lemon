"""WebNLG loading helpers.

The current Hugging Face ``datasets`` 4.x line no longer supports legacy dataset
loading scripts. ``GEM/web_nlg`` still has a script on the main branch, so this
loader uses the Hub's parquet conversion branch instead.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

WEBNLG_PARQUET_TEMPLATE = (
    "hf://datasets/GEM/web_nlg@refs/convert/parquet/{language}/{split}/*.parquet"
)


def webnlg_parquet_files(language: str = "en") -> dict[str, str]:
    """Return parquet data files for WebNLG train and validation splits."""

    return {
        "train": WEBNLG_PARQUET_TEMPLATE.format(language=language, split="train"),
        "validation": WEBNLG_PARQUET_TEMPLATE.format(language=language, split="validation"),
    }


def load_webnlg_parquet(language: str = "en") -> Any:
    """Load WebNLG from parquet conversion files.

    The import is lazy so normal unit tests do not require the research extras.
    """

    try:
        from datasets import load_dataset
    except ImportError as exc:  # pragma: no cover - depends on optional extras
        raise RuntimeError(
            "WebNLG loading requires research dependencies: pip install -e '.[research]'"
        ) from exc

    return load_dataset("parquet", data_files=webnlg_parquet_files(language))


def get_split(dataset: Mapping[str, Any], preferred: str) -> Any:
    """Get a split by preferred name with train/dev naming fallbacks."""

    aliases = {
        "train": ("train",),
        "dev": ("dev", "validation", "valid"),
        "validation": ("validation", "dev", "valid"),
        "test": ("test",),
    }
    for key in aliases.get(preferred, (preferred,)):
        if key in dataset:
            return dataset[key]
    raise KeyError(f"Split {preferred!r} not found. Available: {list(dataset.keys())}")


def take_rows(split: Any, limit: int | None = None) -> list[dict[str, Any]]:
    """Convert the first ``limit`` rows of a Hugging Face split to dictionaries."""

    size = len(split) if limit is None else min(limit, len(split))
    return [dict(split[i]) for i in range(size)]
