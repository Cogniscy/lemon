"""Factor-based similarity and semantic coverage metrics."""

from __future__ import annotations

from collections.abc import Iterable

from lemon_factor.factors.schema import FactorComponent, FactorDecomposition


def _to_factor_weights(
    decomposition: FactorDecomposition | Iterable[FactorComponent],
    *,
    role_aware: bool,
) -> dict[tuple[str, str | None], float]:
    components = (
        decomposition.components
        if isinstance(decomposition, FactorDecomposition)
        else list(decomposition)
    )
    weights: dict[tuple[str, str | None], float] = {}
    for component in components:
        key = (component.factor, component.role if role_aware else None)
        weights[key] = weights.get(key, 0.0) + component.weight
    return weights


def factor_overlap_weight(
    left: FactorDecomposition,
    right: FactorDecomposition,
    *,
    role_aware: bool = False,
) -> float:
    """Return shared factor mass using min-overlap."""

    lw = _to_factor_weights(left, role_aware=role_aware)
    rw = _to_factor_weights(right, role_aware=role_aware)
    return sum(min(lw[k], rw[k]) for k in lw.keys() & rw.keys())


def factor_sim(
    left: FactorDecomposition,
    right: FactorDecomposition,
    *,
    role_aware: bool = False,
) -> float:
    """Symmetric factor similarity.

    Uses shared factor mass divided by the larger of the two factor masses.
    This makes generic-vs-specific matches partial, not perfect.
    """

    left_total = sum(c.weight for c in left.components)
    right_total = sum(c.weight for c in right.components)
    denom = max(left_total, right_total)
    if denom == 0:
        return 0.0
    return factor_overlap_weight(left, right, role_aware=role_aware) / denom


def asymmetric_cover(
    source: FactorDecomposition,
    candidate: FactorDecomposition,
    *,
    role_aware: bool = False,
) -> float:
    """Coverage of source semantics by candidate semantics.

    This is the main LEMON-Factor primitive: text/source fact semantics are
    treated as the denominator, and graph/candidate semantics cover them.
    """

    denom = sum(c.weight for c in source.components)
    if denom == 0:
        return 0.0
    return factor_overlap_weight(source, candidate, role_aware=role_aware) / denom
