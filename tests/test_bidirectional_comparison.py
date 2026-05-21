from lemon_factor.analysis.bidirectional_comparison import build_bidirectional_comparison, write_bidirectional_table


def test_bidirectional_comparison_contains_main_methods(tmp_path):
    report = build_bidirectional_comparison(
        forward={"examples": 2, "edges": 3, "lemon_factor_coverage": 0.8},
        reverse={"reverse_lemon_coverage": 0.7},
        mine_style={"mine_style_score": 0.6},
        baseline={"lexical_graph_text_baselines": {"token_cosine": 0.5, "token_jaccard": 0.4}},
    )
    methods = {row["method"] for row in report["rows"]}
    assert "Forward LEMON-Factor" in methods
    assert "Reverse LEMON-Factor" in methods
    assert "MINE-style nodes/edges" in methods
    path = tmp_path / "table.md"
    write_bidirectional_table(report, path)
    assert "MINE-style" in path.read_text(encoding="utf-8")
