from lemon_factor.coverage.error_analysis import build_error_report, classify_edge_error


def test_classify_missing_decomposition_first():
    row = {"score": 0.0, "missing_decomposition": True, "predicate_cue_score": 0.0}
    assert classify_edge_error(row) == "missing_decomposition"


def test_build_error_report_counts_types():
    rows = [
        {"score": 0.0, "missing_decomposition": True, "predicate": "p"},
        {"score": 0.2, "missing_decomposition": False, "predicate_cue_score": 0.0, "predicate": "q"},
        {"score": 0.8, "missing_decomposition": False, "predicate": "r"},
    ]
    report = build_error_report(rows)
    assert report.low_coverage_edges == 2
    assert report.error_counts["missing_decomposition"] == 1
    assert report.error_counts["missing_lexical_cue"] == 1
