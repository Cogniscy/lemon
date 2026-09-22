import csv
import io
import json
from pathlib import Path

import pytest

from lemon_factor.analysis.expert_review import FIELDS, repair_separators, summarize


def row(reviewer, unit, expert, lemon="preserved"):
    return dict(zip(FIELDS, [reviewer, "example", unit, "demo", "case",
        "A | relation | B", "A relates to B.", "relation", "predicate_meaning", 1.0, lemon, expert]))


def test_quoted_literal_newlines_are_not_reinterpreted():
    raw = 'name,comment\\n"A","keep \\n literal"\\n"B","quote ""inside"""'
    repaired = repair_separators(raw)
    values = list(csv.DictReader(io.StringIO(repaired)))
    assert len(values) == 2
    assert values[0]["comment"] == "keep \\n literal"
    assert values[1]["comment"] == 'quote "inside"'


def test_known_disagreement_statistics():
    ratings = [row("a","one","preserved"),row("b","one","preserved"),
               row("a","two","preserved"),row("b","two","lost")]
    report = summarize(ratings)
    assert report["exact_agreement"] == 0.75
    assert report["pooled_cohen_kappa"] == pytest.approx(0)
    assert report["fleiss_kappa"] == pytest.approx(-1/3)
    assert report["krippendorff_alpha_ordinal"] == pytest.approx(0)
    assert report["krippendorff_alpha_interval_rank"] == pytest.approx(0)
    assert summarize(list(reversed(ratings))) == report


def test_incomplete_and_inconsistent_matrices_fail():
    with pytest.raises(ValueError,match="same two"):
        summarize([row("a","one","preserved")])
    ratings = [row("a","one","preserved"),row("b","one","lost",lemon="lost")]
    with pytest.raises(ValueError,match="Inconsistent"):
        summarize(ratings)


def test_anonymized_pilot_reproduces_saved_report():
    path = Path("annotation/expert_trace_review")
    ratings = list(csv.DictReader(io.StringIO((path/"ratings.csv").read_text(encoding="utf-8"))))
    report = summarize(ratings)
    expected = json.loads((path/"summary.json").read_text(encoding="utf-8"))
    # JSON converts the declared tuple of categories to a list.
    assert json.loads(json.dumps(report)) == expected
    assert report["exact_matches"] == 119
    assert report["judgments"] == 140
    assert report["majority_rows"] == 28
    assert report["majority_matches"] == 27
    assert {r["reviewer_id"] for r in ratings} == {"R1","R2","R3","R4"}
