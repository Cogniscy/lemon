"""Deterministic text evidence helpers for LEMON-Factor coverage.

These helpers intentionally avoid LLM calls. They provide a reproducible first
baseline for matching graph labels, predicate lexical cues, and factor cues in a
WebNLG verbalization.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

_CAMEL_BOUNDARY_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")

_STOP_TOKENS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "was",
    "were",
    "with",
}


def split_camel_case(value: str) -> str:
    """Insert spaces into a camelCase or PascalCase identifier."""

    return _CAMEL_BOUNDARY_RE.sub(" ", value)


def normalize_text(text: str) -> str:
    """Normalize text for simple lexical matching.

    The function lowercases, expands underscores/slashes/camelCase, removes
    punctuation, and collapses whitespace.
    """

    expanded = split_camel_case(text.replace("_", " ").replace("/", " "))
    normalized = _NON_ALNUM_RE.sub(" ", expanded.lower())
    return " ".join(normalized.split())


def text_tokens(text: str, *, keep_stopwords: bool = False) -> list[str]:
    """Return normalized tokens, optionally dropping common stop tokens."""

    tokens = normalize_text(text).split()
    if keep_stopwords:
        return tokens
    return [token for token in tokens if token not in _STOP_TOKENS]


def _contains_phrase(needle: str, haystack: str) -> bool:
    if not needle:
        return False
    return f" {needle} " in f" {haystack} "


def label_in_text(label: str, text: str) -> bool:
    """Return true if a label or a meaningful part of it is present in text."""

    label_norm = normalize_text(label)
    text_norm = normalize_text(text)
    if _contains_phrase(label_norm, text_norm):
        return True
    tokens = text_tokens(label)
    text_token_set = set(text_tokens(text))
    if not tokens:
        return False
    # WebNLG labels can be long entity identifiers. A meaningful token overlap is
    # acceptable evidence at this baseline stage.
    return bool(set(tokens) & text_token_set)


def token_overlap_score(label: str, text: str) -> float:
    """Compute token recall of label tokens covered by text tokens."""

    label_token_set = set(text_tokens(label))
    if not label_token_set:
        return 0.0
    text_token_set = set(text_tokens(text))
    return len(label_token_set & text_token_set) / len(label_token_set)


def cue_in_text(cue: str, text: str) -> bool:
    """Return true if a lexical cue appears in the normalized text."""

    cue_norm = normalize_text(cue)
    if not cue_norm:
        return False
    text_norm = normalize_text(text)
    cue_tokens = cue_norm.split()
    if len(cue_tokens) == 1 and cue_tokens[0] in _STOP_TOKENS:
        # A standalone cue like "in" is too weak to count alone.
        return False
    return _contains_phrase(cue_norm, text_norm)


def any_cue_in_text(cues: Iterable[str], text: str) -> bool:
    """Return true if any non-weak cue is found in text."""

    return any(cue_in_text(cue, text) for cue in cues)


def factor_to_cues(factor_id: str) -> list[str]:
    """Generate simple lexical cues from a semantic factor id."""

    base = normalize_text(factor_id)
    cues = [base]
    if base.endswith(" relation"):
        cues.append(base.removesuffix(" relation").strip())
    return [cue for cue in cues if cue]
