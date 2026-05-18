from __future__ import annotations

from lemon_factor.datasets.sampling import stratified_sample, take_first


def _records() -> list[dict[str, str]]:
    return [
        {"id": "a1", "category": "A"},
        {"id": "a2", "category": "A"},
        {"id": "a3", "category": "A"},
        {"id": "b1", "category": "B"},
        {"id": "b2", "category": "B"},
        {"id": "c1", "category": "C"},
    ]


def test_take_first_preserves_order() -> None:
    assert [record["id"] for record in take_first(_records(), 3)] == ["a1", "a2", "a3"]


def test_take_first_none_returns_all() -> None:
    assert len(take_first(_records(), None)) == 6


def test_stratified_sample_is_deterministic() -> None:
    first = stratified_sample(_records(), 5, seed=7)
    second = stratified_sample(_records(), 5, seed=7)
    assert first == second


def test_stratified_sample_covers_multiple_categories() -> None:
    sampled = stratified_sample(_records(), 3, seed=1)
    categories = {record["category"] for record in sampled}
    assert len(categories) == 3


def test_stratified_sample_handles_small_categories() -> None:
    sampled = stratified_sample(_records(), 10, seed=1)
    assert len(sampled) == 6
    assert {record["id"] for record in sampled} == {record["id"] for record in _records()}


def test_stratified_sample_missing_category() -> None:
    sampled = stratified_sample([{"id": "x"}, {"id": "y", "category": "Y"}], 2, seed=1)
    assert len(sampled) == 2
