from lemon_factor.coverage.expand_lexical_cues import cues_from_predicate, expand_lexical_cues
from lemon_factor.coverage.missing_analysis import MissingPredicateItem, MissingPredicateReport


def test_cues_from_predicate_adds_templates():
    cues = cues_from_predicate("manufacturer")
    assert "manufactured by" in cues
    assert "made by" in cues


def test_expand_lexical_cues_preserves_existing_and_adds_missing():
    missing = MissingPredicateReport(
        total_missing_edges=1,
        predicate_count=1,
        predicates={"author": MissingPredicateItem(predicate="author", count=1)},
    )
    cues = expand_lexical_cues({"author": ["by"]}, missing)
    assert "author" in cues
    assert "written by" in cues["author"]
    assert "by" in cues["author"]
