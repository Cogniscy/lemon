"""Build deterministic seed predicate decompositions from a factor inventory."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Iterable

from lemon_factor.factors.decomposition import (
    FactorComponent,
    PredicateDecomposition,
    PredicateDecompositionSet,
    write_factor_schema,
)
from lemon_factor.factors.inventory import FactorInventory, PredicateInventoryItem
from lemon_factor.factors.seed_schema import build_default_factor_schema

PERSON_CATEGORIES = {"Astronaut", "Artist", "Athlete", "Politician"}
PLACE_CATEGORIES = {"Airport", "Building", "City", "Monument"}
ORG_CATEGORIES = {"Company", "SportsTeam", "University"}
CREATIVE_CATEGORIES = {"ComicsCharacter", "Food", "WrittenWork", "Artist"}
ASTRO_CATEGORIES = {"CelestialBody"}
TRANSPORT_CATEGORIES = {"Airport", "MeanOfTransportation"}
SPORTS_CATEGORIES = {"Athlete", "SportsTeam"}


def _tokens(item: PredicateInventoryItem) -> set[str]:
    return {token.lower() for token in item.candidate_factors}


def _category_counter(item: PredicateInventoryItem) -> Counter[str]:
    return Counter(item.categories)


def _dominant_category_group(item: PredicateInventoryItem) -> str:
    categories = set(item.categories)
    scores = {
        "person": sum(item.categories.get(c, 0) for c in PERSON_CATEGORIES),
        "place": sum(item.categories.get(c, 0) for c in PLACE_CATEGORIES),
        "organization": sum(item.categories.get(c, 0) for c in ORG_CATEGORIES),
        "creative_work": sum(item.categories.get(c, 0) for c in CREATIVE_CATEGORIES),
        "astronomy": sum(item.categories.get(c, 0) for c in ASTRO_CATEGORIES),
        "transport": sum(item.categories.get(c, 0) for c in TRANSPORT_CATEGORIES),
        "sports": sum(item.categories.get(c, 0) for c in SPORTS_CATEGORIES),
    }
    best, count = max(scores.items(), key=lambda pair: (pair[1], pair[0]))
    if count == 0 and categories:
        return "entity"
    return best


def _subject_factor(item: PredicateInventoryItem) -> str:
    group = _dominant_category_group(item)
    if group == "person":
        return "person"
    if group in {"place", "transport", "astronomy"}:
        return "place" if group != "astronomy" else "entity"
    if group == "organization":
        return "organization"
    if group == "creative_work":
        return "creative_work"
    if group == "sports":
        return "person" if "Athlete" in item.categories else "organization"
    return "entity"


def _object_factor_from_tokens(tokens: set[str], fallback: str = "entity") -> str:
    if {"place", "location", "city", "country", "capital", "headquarter", "seat", "birth", "death"} & tokens:
        if "date" in tokens or "year" in tokens:
            return "time"
        return "place"
    if {"date", "year", "period", "epoch"} & tokens:
        return "time"
    if {"length", "feet", "elevation", "number", "area", "population", "density"} & tokens:
        return "quantity"
    if {"language"} & tokens:
        return "language"
    if {"identifier", "icao", "id"} & tokens:
        return "identifier"
    if {"leader", "mayor", "chief", "creator", "author", "artist"} & tokens:
        return "person"
    if {"club", "team", "band", "organisation", "organization", "affiliation", "label"} & tokens:
        return "organization"
    if {"book", "work", "comic", "character"} & tokens:
        return "creative_work"
    return fallback


def _make_components(
    relation: str,
    subject: str,
    obj: str,
    *,
    relation_weight: float = 0.5,
) -> list[FactorComponent]:
    subject_weight = round((1.0 - relation_weight) * 0.4, 6)
    object_weight = round(1.0 - relation_weight - subject_weight, 6)
    return [
        FactorComponent(factor=relation, role="predicate_meaning", weight=relation_weight),
        FactorComponent(factor=subject, role="subject_domain", weight=subject_weight),
        FactorComponent(factor=obj, role="object_domain", weight=object_weight),
    ]


def classify_predicate(item: PredicateInventoryItem) -> tuple[str, str, str, float]:
    """Return relation factor, subject factor, object factor, confidence."""

    tokens = _tokens(item)
    predicate_lc = item.predicate.lower()
    subject = _subject_factor(item)

    if {"birth", "death", "nationality", "occupation"} & tokens or predicate_lc in {
        "birthplace",
        "birthdate",
        "deathplace",
        "deathdate",
    }:
        obj = _object_factor_from_tokens(tokens, fallback="entity")
        if "nationality" in tokens:
            obj = "place"
        return "biographical_relation", "person", obj, 0.82

    if {"location", "country", "city", "capital", "place", "region", "headquarter", "seat"} & tokens:
        relation = "political_relation" if "capital" in tokens else "location_relation"
        obj = _object_factor_from_tokens(tokens, fallback="place")
        return relation, subject, obj, 0.78

    if item.predicate == "isPartOf" or {"part"} & tokens:
        return "part_whole_relation", subject, "entity", 0.82

    if {"leader", "mayor", "chief", "title"} & tokens:
        obj = "person" if not ({"title"} & tokens) else "entity"
        return "political_relation", subject, obj, 0.78

    if {"club", "team", "affiliation", "member", "band", "associated"} & tokens:
        relation = "creative_relation" if {"band", "musical", "artist"} & tokens else "membership_relation"
        obj = _object_factor_from_tokens(tokens, fallback="organization")
        return relation, subject, obj, 0.74

    if {"creator", "author", "artist", "musical", "label", "genre"} & tokens:
        obj = _object_factor_from_tokens(tokens, fallback="person")
        return "creative_relation", subject, obj, 0.74

    if {"orbital", "epoch", "apoapsis", "periapsis", "mass", "temperature"} & tokens or "CelestialBody" in item.categories:
        obj = _object_factor_from_tokens(tokens, fallback="quantity")
        if {"epoch", "period"} & tokens:
            obj = "time"
        return "astronomical_relation", "entity", obj, 0.78

    if {"runway", "elevation", "feet", "length", "surface", "transport"} & tokens:
        obj = _object_factor_from_tokens(tokens, fallback="measurement")
        return "transport_relation", subject, obj, 0.78

    if {"language"} & tokens:
        return "language_relation", subject, "language", 0.82

    if {"identifier", "icao", "id"} & tokens:
        return "identifier_relation", subject, "identifier", 0.82

    if {"organisation", "organization", "company", "operator", "operating", "product"} & tokens:
        obj = _object_factor_from_tokens(tokens, fallback="organization")
        return "organizational_relation", subject, obj, 0.70

    return "entity_relation", subject, _object_factor_from_tokens(tokens), 0.45


def decompose_predicate(item: PredicateInventoryItem) -> PredicateDecomposition:
    relation, subject, obj, confidence = classify_predicate(item)
    source = "fallback" if relation == "entity_relation" else "seed_rule"
    return PredicateDecomposition(
        predicate=item.predicate,
        components=_make_components(relation, subject, obj),
        source=source,
        confidence=confidence,
        evidence={
            "count": item.count,
            "categories": item.categories,
            "candidate_factors": item.candidate_factors,
            "examples": item.examples[:3],
        },
    )


def build_seed_decomposition_set(
    inventory: FactorInventory,
    *,
    top_k: int = 50,
) -> PredicateDecompositionSet:
    factors = build_default_factor_schema()
    top_items = sorted(
        inventory.predicates.values(), key=lambda item: (-item.count, item.predicate)
    )[:top_k]
    decompositions = {item.predicate: decompose_predicate(item) for item in top_items}
    return PredicateDecompositionSet(
        factors=factors,
        decompositions=decompositions,
        metadata={
            "dataset": inventory.dataset,
            "split": inventory.split,
            "examples": inventory.examples,
            "top_k": top_k,
            "source_inventory_predicate_count": len(inventory.predicates),
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", help="Input WebNLG factor inventory JSON")
    parser.add_argument("--schema-out", default="data/interim/factor_schema_seed.json")
    parser.add_argument(
        "--decompositions-out",
        default="data/interim/webnlg_predicate_decompositions_seed.json",
    )
    parser.add_argument("--top-k", type=int, default=50)
    args = parser.parse_args()

    inventory = FactorInventory.from_json_file(args.inventory)
    decomposition_set = build_seed_decomposition_set(inventory, top_k=args.top_k)
    write_factor_schema(args.schema_out, decomposition_set.factors)
    decomposition_set.to_json_file(args.decompositions_out)
    print(
        json.dumps(
            {"schema": args.schema_out, "decompositions": args.decompositions_out},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
