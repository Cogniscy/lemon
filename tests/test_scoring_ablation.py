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
from lemon_factor.scoring.ablate import ablate_reports, render_latex_table
from lemon_factor.scoring.score_perturbations import score_file


def _inventory(tmp_path: Path) -> Path:
    inv = PredicateDecompositionSet(
        schema_version="test-v1",
        factors=[
            SemanticFactor(id="chemical", label="Chemical", allowed_roles=["subject_domain"]),
            SemanticFactor(id="gene_or_protein", label="Gene/protein", allowed_roles=["object_domain"]),
            SemanticFactor(id="inhibition_relation", label="Inhibition", allowed_roles=["predicate_meaning"]),
            SemanticFactor(id="negative_polarity", label="Negative polarity", allowed_roles=["modifier"]),
            SemanticFactor(id="direct_evidence", label="Direct evidence", allowed_roles=["modifier"]),
        ],
        decompositions={
            "chemical_inhibits_gene_or_protein": PredicateDecomposition(
                predicate="chemical_inhibits_gene_or_protein",
                components=[
                    FactorComponent(factor="chemical", role="subject_domain", weight=0.20),
                    FactorComponent(factor="gene_or_protein", role="object_domain", weight=0.20),
                    FactorComponent(factor="inhibition_relation", role="predicate_meaning", weight=0.30),
                    FactorComponent(factor="negative_polarity", role="modifier", weight=0.20),
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


def test_ablation_report_uses_scoring_report_paths(tmp_path: Path) -> None:
    inv = _inventory(tmp_path)
    input_path = tmp_path / "perturbed.jsonl"
    input_path.write_text(json.dumps(_record("polarity_flip").model_dump(mode="json")) + "\n", encoding="utf-8")

    scoring = score_file(input_path, inv, dataset="drugprot")
    scoring_path = tmp_path / "scoring.json"
    scoring_path.write_text(json.dumps(scoring), encoding="utf-8")

    report = ablate_reports([scoring_path])
    assert report["status"] == "passed"
    rows = {row["ablation"]: row["datasets"]["drugprot"]["mean_drop"] for row in report["summary"]}
    assert rows["full"] > rows["minus_polarity"]
    assert rows["label_only"] >= 0.0

    table = render_latex_table(report, caption="Ablation", label="tab:ablation")
    assert "\\caption{Ablation}" in table
    assert "LEMON-full" in table
