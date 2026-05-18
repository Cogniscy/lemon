"""Candidate semantic factor extraction from graph predicate names.

This module deliberately extracts *candidate* factors, not final semantic
factors. WebNLG predicates are mostly DBpedia-style property names such as
``birthPlace`` or ``elevationAboveTheSeaLevel``. Splitting them gives an
interpretable first approximation for later factor-schema construction.
"""

from __future__ import annotations

import re

_BOUNDARY_RE = re.compile(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
_NON_WORD_RE = re.compile(r"[^A-Za-z]+")
_LEADING_ORDINAL_RE = re.compile(r"^\d+(st|nd|rd|th)?", re.IGNORECASE)


def split_camel_case(value: str) -> list[str]:
    """Split a camelCase/PascalCase token into lower-case word pieces.

    Numeric ordinal prefixes are dropped because they are usually WebNLG field
    variants rather than stable semantic factors, e.g. ``1stRunwayLengthFeet``.
    """

    normalized = _LEADING_ORDINAL_RE.sub("", value.strip())
    if not normalized:
        return []
    pieces: list[str] = []
    for chunk in _BOUNDARY_RE.split(normalized):
        chunk = chunk.strip()
        if not chunk:
            continue
        pieces.append(chunk.lower())
    return pieces


def split_predicate_name(predicate: str) -> list[str]:
    """Split DBpedia/WebNLG predicate names into candidate word pieces.

    Supports slashes, underscores, hyphens, digits, and camelCase. Empty pieces
    are removed while duplicate pieces are preserved; repeated evidence is useful
    when summarizing raw candidate-factor frequency.
    """

    pieces: list[str] = []
    for raw_part in predicate.split("/"):
        for token in _NON_WORD_RE.split(raw_part):
            if not token:
                continue
            pieces.extend(split_camel_case(token))
    return [piece for piece in pieces if piece]


def candidate_factors_from_predicate(predicate: str, *, keep_stopwords: bool = True) -> list[str]:
    """Return candidate semantic factors derived from a predicate name.

    The default keeps stopword-like pieces such as ``the`` because they can be
    useful for auditing the splitter. Downstream summary code can decide whether
    to filter them.
    """

    candidates = split_predicate_name(predicate)
    if keep_stopwords:
        return candidates
    stopwords = {"a", "an", "and", "by", "in", "of", "on", "the", "to"}
    return [candidate for candidate in candidates if candidate not in stopwords]
