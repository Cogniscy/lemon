"""Deterministic baseline scoring for perturbed graph--text records."""

from lemon_factor.scoring.baselines import lemon_factor_proxy_score, score_record

__all__ = ["score_record", "lemon_factor_proxy_score"]
