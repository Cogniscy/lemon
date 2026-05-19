import json
from pathlib import Path

from lemon_factor.coverage.run_webnlg_coverage import main
from lemon_factor.datasets.unified_io import write_jsonl
from lemon_factor.factors.decomposition import (
    FactorComponent,
    PredicateDecomposition,
    PredicateDecompositionSet,
    SemanticFactor,
)
from lemon_factor.schema.graphtext import Edge, GraphTextExample, Node, Split


def write_fixture_files(tmp_path: Path):
    example = GraphTextExample(
        id="ex1",
        dataset="webnlg",
        split=Split.dev,
        text="Alan Bean was born in Wheeler, Texas.",
        nodes=[Node(id="n1", label="Alan Bean"), Node(id="n2", label="Wheeler Texas")],
        edges=[Edge(subj="n1", pred="birthPlace", obj="n2")],
    )
    jsonl = tmp_path / "webnlg_dev.jsonl"
    write_jsonl(jsonl, [example])
    factors = [
        SemanticFactor(
            id="biographical_relation",
            label="Biographical relation",
            allowed_roles=["predicate_meaning"],
        ),
        SemanticFactor(id="person", label="Person", allowed_roles=["subject_domain"]),
        SemanticFactor(id="place", label="Place", allowed_roles=["object_domain"]),
    ]
    decomposition = PredicateDecomposition(
        predicate="birthPlace",
        components=[
            FactorComponent(factor="biographical_relation", role="predicate_meaning", weight=0.45),
            FactorComponent(factor="person", role="subject_domain", weight=0.2),
            FactorComponent(factor="place", role="object_domain", weight=0.35),
        ],
    )
    decomposition_path = tmp_path / "decompositions.json"
    PredicateDecompositionSet(
        factors=factors,
        decompositions={"birthPlace": decomposition},
    ).to_json_file(decomposition_path)
    cues_path = tmp_path / "cues.json"
    cues_path.write_text(json.dumps({"birthPlace": ["born in"]}), encoding="utf-8")
    return jsonl, decomposition_path, cues_path


def test_webnlg_coverage_cli_writes_outputs(tmp_path):
    jsonl, decomp, cues = write_fixture_files(tmp_path)
    out = tmp_path / "report.json"
    details = tmp_path / "details.jsonl"
    table = tmp_path / "table.md"
    main(
        [
            str(jsonl),
            "--decompositions",
            str(decomp),
            "--lexical-cues",
            str(cues),
            "--out",
            str(out),
            "--details",
            str(details),
            "--table",
            str(table),
        ]
    )
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["examples"] == 1
    assert report["lemon_factor_coverage"] > 0.9
    assert details.read_text(encoding="utf-8").strip()
    assert "LEMON-Factor coverage" in table.read_text(encoding="utf-8")
