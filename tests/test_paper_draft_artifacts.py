from pathlib import Path


def test_paper_draft_contains_requested_authors():
    main = Path("paper/main.tex").read_text(encoding="utf-8")
    for expected in [
        "Anton Tomilov",
        "Daria Gineva",
        "Danil Tirskikh",
        "Olesia Koroteeva",
        "Yuri Matveev",
    ]:
        assert expected in main
    assert "STC-Innovation" in main
    assert "ITMO University" in main
    assert "affiliation to be confirmed" not in main


def test_paper_draft_sections_exist():
    required = [
        "01_introduction.tex",
        "02_related_work.tex",
        "03_method.tex",
        "04_data.tex",
        "05_experiments.tex",
        "06_results.tex",
        "08_limitations.tex",
        "09_conclusion.tex",
    ]
    for name in required:
        path = Path("paper/sections") / name
        assert path.exists(), name
        assert path.read_text(encoding="utf-8").strip(), name


def test_paper_bibliography_contains_key_related_work():
    bib = Path("paper/references.bib").read_text(encoding="utf-8")
    for key in [
        "gardent2017webnlg",
        "zhang2023factspotter",
        "dhingra2019parent",
        "min2023factscore",
        "zheng2023mtbench",
    ]:
        assert key in bib


def test_method_clarifies_factor_inventory_weights_and_examples():
    method = Path("paper/sections/03_method.tex").read_text(encoding="utf-8")
    assert "manually specified diagnostic resources" in method
    assert "auditable design choices" in method
    assert "\\input{figures/figure_predicate_factor_evaluation}" in method

    figure = Path("paper/figures/figure_predicate_factor_evaluation.tex").read_text(encoding="utf-8")
    assert "figure_factor_scoring_examples.pdf" in figure
    assert "Worked examples of factor-level scoring" in figure
    assert Path("paper/figures/figure_factor_scoring_examples.pdf").exists()
    assert Path("paper/figures/figure_factor_scoring_examples.png").exists()


def test_diagnostic_profile_uses_black_method_labels():
    script = Path("scripts/make_radar_profile.py").read_text(encoding="utf-8")
    assert "ROW_TEXT_COLORS" not in script
    assert 'label.set_color("black")' in script


def test_paper_draft_uses_lemon_name_and_repo():
    main = Path("paper/main.tex").read_text(encoding="utf-8")
    assert "LEMON: Factor-Level Semantic Alignment" in main
    assert "Linguistically Enriched Measure of Ontological Normalization" in main
    assert "https://github.com/Cogniscy/lemon" in main
    assert "LEMON-Factor:" not in main
