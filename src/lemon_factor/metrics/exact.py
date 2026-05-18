"""Small exact/lemma-style baselines for the pilot."""

from __future__ import annotations

import re
import unicodedata

_TOKEN_RE = re.compile(r"[\w-]+", re.UNICODE)


def normalize_surface(text: str) -> str:
    """Lowercase, normalize unicode, and collapse token spacing."""

    normalized = unicodedata.normalize("NFKC", text).lower()
    return " ".join(_TOKEN_RE.findall(normalized))


def exact_match(left: str, right: str) -> float:
    return float(normalize_surface(left) == normalize_surface(right))


def token_jaccard(left: str, right: str) -> float:
    left_tokens = set(normalize_surface(left).split())
    right_tokens = set(normalize_surface(right).split())
    if not left_tokens and not right_tokens:
        return 1.0
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
