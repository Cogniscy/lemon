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
        "07_error_analysis.tex",
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
