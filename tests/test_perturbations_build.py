from __future__ import annotations

import json
from pathlib import Path

from lemon_factor.perturbations.build import build_perturbations
from lemon_factor.perturbations.rules import build_perturbed_record
from lemon_factor.perturbations.schema import PerturbedGraphTextRecord
from lemon_factor.schema.graphtext import GraphTextExample


def _example() -> GraphTextExample:
    return GraphTextExample.model_validate(
        {
            "id": "x1",
            "dataset": "drugprot",
            "split": "train",
            "text": "Drug X inhibits protein Y.",
            "language": "en",
            "nodes": [
                {"id": "c", "label": "Drug X", "type": "Chemical", "aliases": [], "external_ids": {}, "metadata": {}},
                {"id": "g", "label": "protein Y", "type": "Gene", "aliases": [], "external_ids": {}, "metadata": {}},
            ],
            "edges": [{"subj": "c", "pred": "chemical_inhibits_gene_or_protein", "obj": "g", "evidence": None, "metadata": {}}],
            "facts": [],
            "metadata": {},
        }
    )


def test_polarity_flip_changes_inhibition_cue() -> None:
    record = build_perturbed_record(_example(), "polarity_flip")
    validated = PerturbedGraphTextRecord.model_validate(record)
    assert validated.variant == "polarity_flip"
    assert "activates" in validated.text
    assert validated.target_factor_groups == ["polarity", "predicate_meaning"]
    assert any(operation.changed for operation in validated.operations)


def test_relation_blur_preserves_graph_but_changes_text() -> None:
    record = build_perturbed_record(_example(), "relation_blur")
    validated = PerturbedGraphTextRecord.model_validate(record)
    assert validated.edges[0]["pred"] == "chemical_inhibits_gene_or_protein"
    assert "affects" in validated.text
    assert validated.original_text == "Drug X inhibits protein Y."


def test_cli_builder_writes_records_and_report(tmp_path: Path) -> None:
    input_path = tmp_path / "input.jsonl"
    output_path = tmp_path / "perturbed.jsonl"
    report_path = tmp_path / "report.json"
    input_path.write_text(_example().model_dump_json() + "\n", encoding="utf-8")
    report = build_perturbations(input_path, output_path, limit=1, report_out=report_path)
    assert report["records_written"] == 5
    rows = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]
    assert {row["variant"] for row in rows} == {
        "node_deletion",
        "edge_deletion",
        "argument_swap",
        "polarity_flip",
        "relation_blur",
    }
    assert json.loads(report_path.read_text(encoding="utf-8"))["status"] == "passed"
