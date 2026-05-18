"""Deterministic sampling helpers for dataset pilots."""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Iterable
from typing import Any

MISSING_LABEL = "__missing__"


def take_first(records: Iterable[dict[str, Any]], n: int | None = None) -> list[dict[str, Any]]:
    """Return the first ``n`` records, preserving input order.

    ``None`` means all records. The function accepts any iterable and returns a
    materialized list so downstream conversion code can iterate more than once.
    """

    if n is None:
        return list(records)
    if n < 0:
        raise ValueError("n must be non-negative or None")
    output: list[dict[str, Any]] = []
    for record in records:
        if len(output) >= n:
            break
        output.append(record)
    return output


def _label(record: dict[str, Any], label_key: str) -> str:
    value = record.get(label_key)
    if value is None or value == "":
        return MISSING_LABEL
    return str(value)


def stratified_sample(
    records: Iterable[dict[str, Any]],
    n: int | None,
    *,
    label_key: str = "category",
    seed: int = 42,
    min_per_label: int = 1,
) -> list[dict[str, Any]]:
    """Return a deterministic, approximately label-balanced sample.

    The sampler is designed for small reproducible pilots rather than exact
    statistical sampling. It groups records by ``label_key``, shuffles labels and
    items with ``seed``, takes up to ``min_per_label`` from each label when the
    requested budget allows it, and then fills the remainder round-robin.

    If ``n`` is ``None``, all records are returned with shuffled within-label and
    round-robin ordering. Small labels are exhausted safely.
    """

    if n is not None and n < 0:
        raise ValueError("n must be non-negative or None")
    if min_per_label < 0:
        raise ValueError("min_per_label must be non-negative")

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[_label(record, label_key)].append(record)

    if not groups or n == 0:
        return []

    rng = random.Random(seed)
    labels = sorted(groups)
    rng.shuffle(labels)
    for values in groups.values():
        rng.shuffle(values)

    target = sum(len(values) for values in groups.values()) if n is None else n
    target = min(target, sum(len(values) for values in groups.values()))
    selected: list[dict[str, Any]] = []
    used = {label: 0 for label in labels}

    # Coverage pass: include up to min_per_label examples per category when the
    # budget is large enough. This prevents early large categories from drowning
    # out smaller categories.
    if min_per_label > 0:
        for _ in range(min_per_label):
            for label in labels:
                if len(selected) >= target:
                    return selected
                if used[label] < len(groups[label]):
                    selected.append(groups[label][used[label]])
                    used[label] += 1

    # Balance pass: fill the remaining budget round-robin.
    while len(selected) < target:
        progressed = False
        for label in labels:
            if len(selected) >= target:
                break
            if used[label] < len(groups[label]):
                selected.append(groups[label][used[label]])
                used[label] += 1
                progressed = True
        if not progressed:
            break

    return selected
