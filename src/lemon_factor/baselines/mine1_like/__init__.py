"""MINE-1-compatible retention baseline.

This module implements the evaluation shape used by KGGen/MINE-1: retrieve a
small graph neighborhood for a reference fact and score whether the fact is
recoverable from that graph.  The local implementation is deliberately
lightweight and auditable; it should be described as MINE-1-compatible or
MINE-inspired unless it is run through the public KGGen/MINE pipeline.
"""

from .core import mine1_score, score_item

__all__ = ["mine1_score", "score_item"]
