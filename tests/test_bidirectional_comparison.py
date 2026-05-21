from lemon_factor.analysis.bidirectional_comparison import (
    build_bidirectional_comparison,
    write_bidirectional_table,
    write_mine_subset_comparison_table,
)


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
    assert "MINE-style composite node/edge" in methods
    path = tmp_path / "table.md"
    write_bidirectional_table(report, path)
    assert "MINE-style" in path.read_text(encoding="utf-8")


def test_bidirectional_comparison_accepts_llm_judged_mine():
    report = build_bidirectional_comparison(
        forward={"examples": 1, "edges": 1, "lemon_factor_coverage": 0.8},
        reverse={"reverse_lemon_coverage": 0.7},
        mine_style={"mine_style_score": 0.6},
        mine_style_llm={"mine_style_score": 0.65, "llm_fact_recoverability": 0.52, "metadata": {"judge_mode": "llm"}},
    )
    llm_rows = [row for row in report["rows"] if row["uses_llm_judge"]]
    assert len(llm_rows) == 1
    assert llm_rows[0]["method"] == "MINE-style LLM fact recoverability"
    assert llm_rows[0]["score_key"] == "llm_fact_recoverability"
    assert llm_rows[0]["score"] == 0.52


def test_mine_subset_comparison_table_separates_score_semantics(tmp_path):
    report = build_bidirectional_comparison(
        forward={"examples": 1, "edges": 1, "lemon_factor_coverage": 0.8},
        reverse={"reverse_lemon_coverage": 0.7},
        mine_style={"mine_style_score": 0.6},
        mine_style_llm={
            "facts": 50,
            "llm_fact_recoverability": 0.52,
            "deterministic_score_on_subset": 0.75,
            "deterministic_node_information_on_subset": 0.96,
            "deterministic_edge_information_on_subset": 0.54,
            "deterministic_fact_recoverability_on_subset": 0.54,
            "judge_agreement_with_deterministic": 0.98,
            "parse_success_rate": 1.0,
            "mean_judge_confidence": 0.5417,
            "metadata": {"judge_mode": "llm"},
        },
    )
    subset = report["mine_subset_comparison"]
    assert subset["deterministic_composite_node_edge_score"] == 0.75
    assert subset["llm_fact_recoverability"] == 0.52
    table = tmp_path / "subset.md"
    write_mine_subset_comparison_table(report, table)
    text = table.read_text(encoding="utf-8")
    assert "Deterministic composite node/edge score" in text
    assert "LLM fact recoverability" in text
