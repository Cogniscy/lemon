import json
import socket

import pytest

from lemon_factor.cli import main
from lemon_factor.demo import build_demo, reproduce_demo
from lemon_factor.coverage.factor_coverage import score_predicate_decomposition
from lemon_factor.factors.decomposition import PredicateDecomposition
from lemon_factor.schema.graphtext import Edge
from lemon_factor.demo import resource_bytes


def test_demo_uses_scorer_without_network(monkeypatch, tmp_path, capsys):
    def forbidden(*args, **kwargs):
        raise AssertionError("Demo must not access the network")
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.chdir(tmp_path)
    assert main(["demo", "--format", "json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report == build_demo()
    assert not list(tmp_path.iterdir())
    source = json.loads(resource_bytes())
    for case in report["cases"]:
        expected = score_predicate_decomposition(
            PredicateDecomposition.model_validate(source["decomposition"]),
            case["text"], Edge.model_validate(source["source_edge"]),
            source["node_labels"], source["lexical_cues"],
        )
        assert case["score"] == expected.score
        assert case["components"] == [c.model_dump() for c in expected.components]
    assert report["cases"][0]["score"] > report["cases"][1]["score"]
    assert all(c["known_limitation"] for c in report["cases"][2:])


def test_cli_invalid_argument(capsys):
    with pytest.raises(SystemExit) as error:
        main(["demo", "--format", "bad"])
    assert error.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_reproduction_preserves_existing_files(tmp_path):
    out = tmp_path / "results"
    reproduce_demo(out)
    before = {p.name: p.read_bytes() for p in out.iterdir()}
    with pytest.raises(FileExistsError):
        reproduce_demo(out)
    assert before == {p.name: p.read_bytes() for p in out.iterdir()}
    reproduce_demo(out, overwrite=True)
    assert before == {p.name: p.read_bytes() for p in out.iterdir()}
    scores = json.loads(before["scores.json"])
    summary = before["summary.md"].decode()
    for case in scores["cases"]:
        assert f"| {case['id']} | {case['score']:.4f} |" in summary
    import hashlib
    manifest = json.loads(before["manifest.json"])
    assert manifest["input_sha256"]["demo_data/cases.json"] == hashlib.sha256(resource_bytes()).hexdigest()


@pytest.mark.parametrize("case_id", ["negation", "other_participant"])
@pytest.mark.xfail(strict=True, reason="Lexical evidence does not resolve negation or bind participants")
def test_semantically_invalid_case_scores_below_correct(case_id):
    scores = {c["id"]: c["score"] for c in build_demo()["cases"]}
    assert scores[case_id] < scores["correct"]
