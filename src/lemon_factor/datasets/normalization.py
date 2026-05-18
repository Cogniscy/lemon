"""Dataset normalization helpers.

The functions here are intentionally conservative: they normalize labels and
identifiers for the unified GraphText format without trying to infer new facts.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


_SEPARATOR_PATTERNS = (
    re.compile(r"^\s*(?P<subj>.*?)\s*\|\s*(?P<pred>.*?)\s*\|\s*(?P<obj>.*?)\s*$"),
    re.compile(r"^\s*\(?\s*(?P<subj>.*?)\s*,\s*(?P<pred>.*?)\s*,\s*(?P<obj>.*?)\s*\)?\s*$"),
    re.compile(r"^\s*(?P<subj>.*?)\s*:\s*(?P<pred>.*?)\s*:\s*(?P<obj>.*?)\s*$"),
)


@dataclass(frozen=True)
class ParsedTriple:
    """A normalized triple parsed from a dataset-specific surface string."""

    subj: str
    pred: str
    obj: str
    raw: str


def stable_id(prefix: str, value: str) -> str:
    """Create a deterministic compact identifier for a label or relation value."""

    digest = hashlib.sha1(value.strip().lower().encode("utf-8")).hexdigest()[:12]
    safe_prefix = re.sub(r"[^a-zA-Z0-9_]+", "_", prefix).strip("_") or "id"
    return f"{safe_prefix}_{digest}"


def clean_label(value: str) -> str:
    """Clean a WebNLG/DBpedia-style label while preserving its meaning."""

    cleaned = value.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {'"', "'"}:
        cleaned = cleaned[1:-1]
    cleaned = cleaned.replace("_", " ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def parse_webnlg_triple(raw: str) -> ParsedTriple:
    """Parse a WebNLG triple surface form.

    Supported forms include the parquet conversion's pipe format:
    ``subject | predicate | object`` and two fallback formats used by older
    WebNLG releases or simple fixtures.
    """

    for pattern in _SEPARATOR_PATTERNS:
        match = pattern.match(raw)
        if match:
            subj = clean_label(match.group("subj"))
            pred = clean_label(match.group("pred"))
            obj = clean_label(match.group("obj"))
            if subj and pred and obj:
                return ParsedTriple(subj=subj, pred=pred, obj=obj, raw=raw)
    raise ValueError(f"Cannot parse WebNLG triple: {raw!r}")
