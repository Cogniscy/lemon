"""Default deterministic seed semantic factor schema for lemon-04."""

from __future__ import annotations

from pathlib import Path

from lemon_factor.factors.decomposition import SemanticFactor, read_factor_schema, write_factor_schema

DOMAIN_ROLES = ["subject_domain", "object_domain", "value_domain", "background"]
RELATION_ROLES = ["predicate_meaning", "modifier", "background"]
ALL_ROLES = [
    "subject_domain",
    "object_domain",
    "predicate_meaning",
    "modifier",
    "value_domain",
    "background",
]


def _factor(
    factor_id: str,
    label: str,
    level: str,
    description: str,
    *,
    allowed_roles: list[str] | None = None,
    parents: list[str] | None = None,
) -> SemanticFactor:
    return SemanticFactor(
        id=factor_id,
        label=label,
        level=level,
        description=description,
        allowed_roles=allowed_roles or ALL_ROLES,
        parents=parents or [],
    )


def build_default_factor_schema() -> list[SemanticFactor]:
    """Return the seed semantic factor vocabulary used in lemon-04.

    The schema is intentionally small. It is not a final ontology; it is a
    controlled first layer that maps WebNLG predicate evidence into reusable
    semantic directions.
    """

    return [
        _factor("entity", "Entity", "universal", "Generic entity or concept.", allowed_roles=DOMAIN_ROLES),
        _factor("person", "Person", "universal", "Human individual or person-like agent.", allowed_roles=DOMAIN_ROLES, parents=["entity"]),
        _factor("place", "Place", "universal", "Location, city, country, region, or spatial object.", allowed_roles=DOMAIN_ROLES, parents=["entity"]),
        _factor("organization", "Organization", "universal", "Institution, company, team, university, or formal group.", allowed_roles=DOMAIN_ROLES, parents=["entity"]),
        _factor("creative_work", "Creative work", "domain", "Work, character, song, book, artwork, or cultural artifact.", allowed_roles=DOMAIN_ROLES, parents=["entity"]),
        _factor("event", "Event", "universal", "Event or historically bounded occurrence.", allowed_roles=DOMAIN_ROLES, parents=["entity"]),
        _factor("time", "Time", "universal", "Date, period, epoch, or temporal value.", allowed_roles=DOMAIN_ROLES),
        _factor("quantity", "Quantity", "universal", "Numeric value, scalar quantity, count, or physical magnitude.", allowed_roles=DOMAIN_ROLES),
        _factor("measurement", "Measurement", "scientific", "Measured property or value-bearing observation.", allowed_roles=DOMAIN_ROLES + ["predicate_meaning"]),
        _factor("language", "Language", "domain", "Natural language or language attribute.", allowed_roles=DOMAIN_ROLES, parents=["entity"]),
        _factor("identifier", "Identifier", "domain", "Code, database identifier, location identifier, or registry key.", allowed_roles=DOMAIN_ROLES),
        _factor("entity_relation", "Entity relation", "abstract_relation", "Generic relation between graph entities.", allowed_roles=RELATION_ROLES),
        _factor("biographical_relation", "Biographical relation", "abstract_relation", "Birth, death, nationality, occupation, and person-level biography facts.", allowed_roles=RELATION_ROLES, parents=["entity_relation"]),
        _factor("location_relation", "Location relation", "abstract_relation", "Spatial containment, location, country, city, or place association.", allowed_roles=RELATION_ROLES, parents=["entity_relation"]),
        _factor("part_whole_relation", "Part-whole relation", "abstract_relation", "Membership, containment, part-of, or whole-part structure.", allowed_roles=RELATION_ROLES, parents=["entity_relation"]),
        _factor("membership_relation", "Membership relation", "abstract_relation", "Affiliation, club, team, membership, or participation relation.", allowed_roles=RELATION_ROLES, parents=["entity_relation"]),
        _factor("political_relation", "Political relation", "abstract_relation", "Leadership, mayor, capital, governance, or office relation.", allowed_roles=RELATION_ROLES, parents=["entity_relation"]),
        _factor("creative_relation", "Creative relation", "abstract_relation", "Creator, author, artist, band, work, or cultural production relation.", allowed_roles=RELATION_ROLES, parents=["entity_relation"]),
        _factor("organizational_relation", "Organizational relation", "abstract_relation", "Company, university, headquarters, operation, or institutional relation.", allowed_roles=RELATION_ROLES, parents=["entity_relation"]),
        _factor("astronomical_relation", "Astronomical relation", "abstract_relation", "Celestial-body and astronomy-specific relation.", allowed_roles=RELATION_ROLES, parents=["entity_relation"]),
        _factor("sports_relation", "Sports relation", "abstract_relation", "Athlete, club, team, ground, or sport competition relation.", allowed_roles=RELATION_ROLES, parents=["entity_relation"]),
        _factor("transport_relation", "Transport relation", "abstract_relation", "Airport, runway, vehicle, infrastructure, or transport relation.", allowed_roles=RELATION_ROLES, parents=["entity_relation"]),
        _factor("language_relation", "Language relation", "abstract_relation", "Language-used, language-of-work, or language attribute relation.", allowed_roles=RELATION_ROLES, parents=["entity_relation"]),
        _factor("identifier_relation", "Identifier relation", "abstract_relation", "Identifier-bearing relation such as ICAO or location codes.", allowed_roles=RELATION_ROLES, parents=["entity_relation"]),
    ]


def save_default_factor_schema(path: str | Path) -> None:
    write_factor_schema(path, build_default_factor_schema())


def load_factor_schema(path: str | Path) -> list[SemanticFactor]:
    return read_factor_schema(path)
