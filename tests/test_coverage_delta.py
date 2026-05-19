from pathlib import Path

from lemon_factor.coverage.run_coverage_delta import write_delta_table


def test_write_delta_table_contains_before_after_delta(tmp_path: Path):
    before = {"scored_edges": 1, "missing_decomposition_rate": 0.5, "lemon_factor_coverage": 0.2}
    after = {"scored_edges": 3, "missing_decomposition_rate": 0.1, "lemon_factor_coverage": 0.6}
    out = tmp_path / "delta.md"
    write_delta_table(before, after, out)
    text = out.read_text(encoding="utf-8")
    assert "Before" in text
    assert "After" in text
    assert "0.4" in text
