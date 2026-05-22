import json
from pathlib import Path

from lemon_factor.calibration.run_calibration import main
from lemon_factor.datasets.unified_io import write_jsonl
from lemon_factor.factors.decomposition import (
    FactorComponent,
    PredicateDecomposition,
    PredicateDecompositionSet,
    SemanticFactor,
)
from lemon_factor.reverse.reconstruct_graph import reconstruct_corpus, write_reconstructed_graphs
from lemon_factor.schema.graphtext import Edge, GraphTextExample, Node, Split


def write_fixture(tmp_path: Path):
    example = GraphTextExample(
        id="ex1",
        dataset="toy",
        split=Split.dev,
        text="Alan Bean was born in Wheeler Texas.",
        nodes=[Node(id="n1", label="Alan Bean"), Node(id="n2", label="Wheeler Texas")],
        edges=[Edge(subj="n1", pred="birthPlace", obj="n2")],
    )
    jsonl = tmp_path / "dev.jsonl"
    write_jsonl(jsonl, [example])
    reconstructed = tmp_path / "reconstructed.jsonl"
    write_reconstructed_graphs(reconstruct_corpus([example], lexical_cues={"birthPlace": ["born in"]}), reconstructed)
    decomp = tmp_path / "decomp.json"
    PredicateDecompositionSet(
        factors=[
            SemanticFactor(id="person", label="Person", allowed_roles=["subject_domain"]),
            SemanticFactor(id="place", label="Place", allowed_roles=["object_domain"]),
            SemanticFactor(id="bio", label="Bio", allowed_roles=["predicate_meaning"]),
        ],
        decompositions={
            "birthPlace": PredicateDecomposition(
                predicate="birthPlace",
                components=[
                    FactorComponent(factor="person", role="subject_domain", weight=0.2),
                    FactorComponent(factor="place", role="object_domain", weight=0.3),
                    FactorComponent(factor="bio", role="predicate_meaning", weight=0.5),
                ],
            )
        },
    ).to_json_file(decomp)
    cues = tmp_path / "cues.json"
    cues.write_text(json.dumps({"birthPlace": ["born in"]}), encoding="utf-8")
    return jsonl, reconstructed, decomp, cues


def test_calibration_cli_writes_perturbed_artifacts(tmp_path: Path):
    jsonl, reconstructed, decomp, cues = write_fixture(tmp_path)
    out = tmp_path / "calibration.json"
    details = tmp_path / "details.jsonl"
    table = tmp_path / "summary.md"
    by_noise = tmp_path / "by_noise.md"
    text_side = tmp_path / "text_side.md"
    graph_side = tmp_path / "graph_side.md"
    relation_deletion = tmp_path / "relation_deletion.md"
    perturbed = tmp_path / "perturbed"
    main(
        [
            str(jsonl),
            "--reconstructed",
            str(reconstructed),
            "--decompositions",
            str(decomp),
            "--lexical-cues",
            str(cues),
            "--noise-types",
            "delete_relation_phrase",
            "drop_edge",
            "--noise-levels",
            "0.0",
            "1.0",
            "--perturbation-dir",
            str(perturbed),
            "--out",
            str(out),
            "--details",
            str(details),
            "--table",
            str(table),
            "--by-noise-table",
            str(by_noise),
            "--text-side-table",
            str(text_side),
            "--graph-side-table",
            str(graph_side),
            "--relation-deletion-table",
            str(relation_deletion),
        ]
    )
    report = json.loads(out.read_text(encoding="utf-8"))
    assert len(report["rows"]) == 4
    assert report["perturbation_dir"] == str(perturbed)
    assert details.read_text(encoding="utf-8").strip()
    assert "recommended_noise_target" not in table.read_text(encoding="utf-8")
    assert "forward_lemon" in table.read_text(encoding="utf-8")
    assert report["summary_by_metric_text_noise"]
    assert report["summary_by_metric_graph_noise"]
    assert report["summary_by_metric_targeted"]
    assert report["relation_deletion_sanity"]
    assert report["rows"][0]["perturbation_quality"] == "clean"
    assert "Text-side" in text_side.read_text(encoding="utf-8")
    assert "Graph-side" in graph_side.read_text(encoding="utf-8")
    assert "surface-control" in relation_deletion.read_text(encoding="utf-8")
    manifests = list(perturbed.rglob("*_manifest.jsonl"))
    assert manifests
