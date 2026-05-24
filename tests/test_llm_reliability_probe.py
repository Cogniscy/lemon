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
from lemon_factor.reliability.mock_judgments import make_mock_judgments
from lemon_factor.reliability.prepare_llm_probe import prepare_probe
from lemon_factor.reliability.schema import LLMProbeItem, LLMProbeJudgment
from lemon_factor.reliability.summarize_llm_probe import summarize


def _inventory(tmp_path: Path) -> Path:
    inv = PredicateDecompositionSet(
        schema_version="test-v1",
        factors=[
            SemanticFactor(id="chemical", label="Chemical", allowed_roles=["subject_domain", "object_domain", "value_domain"]),
            SemanticFactor(id="gene_or_protein", label="Gene/protein", allowed_roles=["subject_domain", "object_domain", "value_domain"]),
            SemanticFactor(id="inhibition_relation", label="Inhibition", allowed_roles=["predicate_meaning", "modifier"]),
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
        metadata={"dataset": "drugprot"},
    )
    path = tmp_path / "drugprot_inventory.json"
    inv.to_json_file(path)
    return path


def _record(idx: int, variant: str = "polarity_flip") -> PerturbedGraphTextRecord:
    return PerturbedGraphTextRecord(
        id=f"r{idx}::perturb::{variant}",
        original_id=f"r{idx}",
        dataset="drugprot",
        split="train",
        variant=variant,
        text="Drug A activates Protein B." if variant == "polarity_flip" else "Drug A affects Protein B.",
        original_text="Drug A inhibits Protein B.",
        nodes=[
            {"id": "c1", "label": "Drug A", "type": "Chemical"},
            {"id": "g1", "label": "Protein B", "type": "Gene"},
        ],
        edges=[{"subj": "c1", "pred": "chemical_inhibits_gene_or_protein", "obj": "g1"}],
        expected_damage=ExpectedDamage(direction="down", severity="high", rationale="test"),
        target_factor_groups=["polarity", "predicate_meaning"] if variant == "polarity_flip" else ["predicate_specificity", "evidence_form"],
        operations=[{"edge_index": 0, "operation": variant, "target": "inhibits", "replacement": "activates", "changed": True}],
    )


def test_prepare_probe_writes_items_and_prompt_payload(tmp_path: Path) -> None:
    inv = _inventory(tmp_path)
    perturbed = tmp_path / "perturbed.jsonl"
    perturbed.write_text("\n".join(json.dumps(_record(i).model_dump(mode="json")) for i in range(4)) + "\n", encoding="utf-8")
    out = tmp_path / "items.jsonl"
    prompts = tmp_path / "prompts.jsonl"
    report = prepare_probe([perturbed], [inv], out=out, prompt_out=prompts, per_dataset=3, seed=7)
    assert report["status"] == "passed"
    assert report["items_written"] == 3
    item = LLMProbeItem.model_validate_json(out.read_text(encoding="utf-8").splitlines()[0])
    assert item.dataset == "drugprot"
    assert item.source_edge.predicate == "chemical_inhibits_gene_or_protein"
    assert item.factors
    prompt_payload = json.loads(prompts.read_text(encoding="utf-8").splitlines()[0])
    assert prompt_payload["required_output_schema"]["item_id"] == item.id


def test_mock_judgments_and_summarizer(tmp_path: Path) -> None:
    inv = _inventory(tmp_path)
    perturbed = tmp_path / "perturbed.jsonl"
    perturbed.write_text("\n".join(json.dumps(_record(i).model_dump(mode="json")) for i in range(2)) + "\n", encoding="utf-8")
    items = tmp_path / "items.jsonl"
    prepare_probe([perturbed], [inv], out=items, per_dataset=2)
    judgments = tmp_path / "judgments.jsonl"
    mock_report = make_mock_judgments(items, judgments, judge_id="mock_strict")
    assert mock_report["judgments"] == 2
    first = LLMProbeJudgment.model_validate_json(judgments.read_text(encoding="utf-8").splitlines()[0])
    assert first.decisions
    summary = summarize(items, [str(judgments)], out=tmp_path / "summary.json")
    assert summary["status"] == "passed"
    assert summary["judgment_count"] == 2
    assert summary["summary"]


def test_summarizer_handles_missing_judgments(tmp_path: Path) -> None:
    inv = _inventory(tmp_path)
    perturbed = tmp_path / "perturbed.jsonl"
    perturbed.write_text(json.dumps(_record(1).model_dump(mode="json")) + "\n", encoding="utf-8")
    items = tmp_path / "items.jsonl"
    prepare_probe([perturbed], [inv], out=items, per_dataset=1)
    summary = summarize(items, [str(tmp_path / "does_not_exist.jsonl")], out=tmp_path / "summary.json")
    assert summary["status"] == "no_judgments"
    assert summary["item_count"] == 1
