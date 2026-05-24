from __future__ import annotations

import json
from pathlib import Path

from lemon_factor.factors.decomposition import (
    FactorComponent,
    PredicateDecomposition,
    PredicateDecompositionSet,
    SemanticFactor,
)
from lemon_factor.perturbations.schema import ExpectedDamage, PerturbedGraphTextRecord
from lemon_factor.scoring.baselines import node_present, predicate_match, score_record
from lemon_factor.scoring.score_perturbations import render_latex_table, score_file


def _inventory(tmp_path: Path) -> Path:
    inv = PredicateDecompositionSet(
        schema_version="test-v1",
        factors=[
            SemanticFactor(
                id="chemical",
                label="Chemical",
                allowed_roles=["subject_domain", "object_domain", "value_domain"],
            ),
            SemanticFactor(
                id="gene_or_protein",
                label="Gene/protein",
                allowed_roles=["subject_domain", "object_domain", "value_domain"],
            ),
            SemanticFactor(
                id="inhibition_relation",
                label="Inhibition",
                allowed_roles=["predicate_meaning", "modifier"],
            ),
            SemanticFactor(
                id="negative_polarity",
                label="Negative polarity",
                allowed_roles=["modifier"],
            ),
            SemanticFactor(
                id="chemical_to_gene_or_protein_direction",
                label="Direction",
                allowed_roles=["modifier"],
            ),
            SemanticFactor(
                id="direct_evidence",
                label="Direct evidence",
                allowed_roles=["modifier"],
            ),
        ],
        decompositions={
            "chemical_inhibits_gene_or_protein": PredicateDecomposition(
                predicate="chemical_inhibits_gene_or_protein",
                components=[
                    FactorComponent(factor="chemical", role="subject_domain", weight=0.15),
                    FactorComponent(factor="gene_or_protein", role="object_domain", weight=0.15),
                    FactorComponent(factor="inhibition_relation", role="predicate_meaning", weight=0.30),
                    FactorComponent(factor="negative_polarity", role="modifier", weight=0.20),
                    FactorComponent(
                        factor="chemical_to_gene_or_protein_direction", role="modifier", weight=0.10
                    ),
                    FactorComponent(factor="direct_evidence", role="modifier", weight=0.10),
                ],
            )
        },
    )
    path = tmp_path / "inventory.json"
    inv.to_json_file(path)
    return path


def _record(variant: str = "polarity_flip") -> PerturbedGraphTextRecord:
    return PerturbedGraphTextRecord(
        id="r1::perturb::polarity",
        original_id="r1",
        dataset="drugprot",
        split="train",
        variant=variant,
        text="Drug A activates Protein B.",
        original_text="Drug A inhibits Protein B.",
        nodes=[
            {"id": "c1", "label": "Drug A", "type": "Chemical"},
            {"id": "g1", "label": "Protein B", "type": "Gene"},
        ],
        edges=[{"subj": "c1", "pred": "chemical_inhibits_gene_or_protein", "obj": "g1"}],
        expected_damage=ExpectedDamage(direction="down", severity="high", rationale="test"),
        target_factor_groups=["polarity", "predicate_meaning"],
        operations=[
            {
                "edge_index": 0,
                "operation": "polarity_flip",
                "target": "inhibits",
                "replacement": "activates",
                "changed": True,
            }
        ],
    )


def test_lexical_helpers_match_biomedical_surface_forms() -> None:
    assert node_present("Drug A inhibits Protein B.", "Drug A")
    assert predicate_match("Drug A inhibits Protein B.", "chemical_inhibits_gene_or_protein") == 1.0
    assert predicate_match("Drug A affects Protein B.", "chemical_inhibits_gene_or_protein") == 0.0


def test_score_record_penalizes_factor_damage(tmp_path: Path) -> None:
    inventory = PredicateDecompositionSet.from_json_file(_inventory(tmp_path))
    scores = score_record(_record(), inventory)
    assert scores["entity_recall"] == 1.0
    assert scores["label_match"] == 0.0
    assert scores["triple_match"] == 0.0
    assert 0.0 < scores["lemon_full"] < 1.0
    assert scores["lemon_full"] < scores["entity_recall"]


def test_score_file_and_table_render(tmp_path: Path) -> None:
    inv = _inventory(tmp_path)
    input_path = tmp_path / "perturbed.jsonl"
    input_path.write_text(json.dumps(_record().model_dump(mode="json")) + "\n", encoding="utf-8")
    report = score_file(input_path, inv, dataset="drugprot")
    assert report["status"] == "passed"
    assert report["record_count"] == 1
    assert report["summary"][0]["metrics"]["lemon_full"] < 1.0
    table = render_latex_table(report["summary"], caption="Test", label="tab:test")
    assert "\\caption{Test}" in table
    assert "LEMON-full" in table
