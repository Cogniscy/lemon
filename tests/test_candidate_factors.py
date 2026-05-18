from __future__ import annotations

from lemon_factor.factors.candidates import (
    candidate_factors_from_predicate,
    split_camel_case,
    split_predicate_name,
)


def test_split_camel_case_simple_predicate() -> None:
    assert split_camel_case("birthPlace") == ["birth", "place"]


def test_split_camel_case_drops_ordinal_prefix() -> None:
    assert split_camel_case("1stRunwayLengthFeet") == ["runway", "length", "feet"]


def test_split_predicate_name_handles_slash() -> None:
    assert split_predicate_name("associatedBand/associatedMusicalArtist") == [
        "associated",
        "band",
        "associated",
        "musical",
        "artist",
    ]


def test_split_predicate_name_handles_sea_level() -> None:
    assert split_predicate_name("elevationAboveTheSeaLevel") == [
        "elevation",
        "above",
        "the",
        "sea",
        "level",
    ]


def test_candidate_factors_can_filter_stopwords() -> None:
    assert candidate_factors_from_predicate("elevationAboveTheSeaLevel", keep_stopwords=False) == [
        "elevation",
        "above",
        "sea",
        "level",
    ]
