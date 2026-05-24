"""Prepare stratified LLM reliability probe items from perturbation files.

The command does not call an LLM. It creates auditable JSONL items and optional
JSONL prompt batches that can be sent to one or more external judges.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from lemon_factor.factors.decomposition import PredicateDecompositionSet
from lemon_factor.perturbations.schema import PerturbedGraphTextRecord
from lemon_factor.reliability.schema import LLMProbeItem, ProbeEdge, ProbeFactor
from lemon_factor.scoring.baselines import score_record

_VARIANT_ORDER = [
    "node_deletion",
    "edge_deletion",
    "argument_swap",
    "polarity_flip",
    "relation_blur",
]


def factor_group(factor_id: str, role: str) -> str:
    """Map a detailed factor component to a judge-facing group."""

    factor = factor_id.casefold()
    role_norm = role.casefold()
    if role_norm in {"subject_domain", "object_domain", "value_domain"}:
        return "participant_roles"
    if "direction" in factor:
        return "directionality"
    if any(token in factor for token in ["polarity", "positive", "negative", "causal"]):
        return "polarity"
    if "evidence" in factor:
        return "evidence_form"
    if role_norm == "predicate_meaning":
        return "predicate_meaning"
    return "background"


def _read_perturbed(path: str | Path) -> list[PerturbedGraphTextRecord]:
    records: list[PerturbedGraphTextRecord] = []
    with Path(path).open("r", encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                records.append(PerturbedGraphTextRecord.model_validate_json(line))
            except Exception as exc:  # pragma: no cover - CLI context
                raise ValueError(f"Invalid perturbation record at {path}:{line_no}") from exc
    return records


def _load_inventories(paths: list[str | Path]) -> dict[str, PredicateDecompositionSet]:
    inventories: dict[str, PredicateDecompositionSet] = {}
    for path in paths:
        inventory = PredicateDecompositionSet.from_json_file(path)
        dataset = str(inventory.metadata.get("dataset") or Path(path).stem)
        inventories[dataset] = inventory
    return inventories


def _node_labels(record: PerturbedGraphTextRecord) -> dict[str, str]:
    return {str(node.get("id", "")): str(node.get("label", "")) for node in record.nodes if node.get("id")}


def _first_edge(record: PerturbedGraphTextRecord) -> dict[str, Any] | None:
    for edge in record.edges:
        if edge.get("pred"):
            return edge
    return None


def _factors_for_predicate(inventory: PredicateDecompositionSet, predicate: str) -> list[ProbeFactor]:
    decomposition = inventory.decompositions.get(predicate)
    if decomposition is None:
        return []
    factor_by_id = {factor.id: factor for factor in inventory.factors}
    factors: list[ProbeFactor] = []
    seen_ids: dict[str, int] = {}
    for component in decomposition.components:
        factor = factor_by_id.get(component.factor)
        label = factor.label if factor else component.factor.replace("_", " ")
        description = factor.description if factor else ""
        base_id = f"{component.factor}::{component.role}"
        seen_ids[base_id] = seen_ids.get(base_id, 0) + 1
        component_id = base_id if seen_ids[base_id] == 1 else f"{base_id}::{seen_ids[base_id]}"
        factors.append(
            ProbeFactor(
                id=component_id,
                label=label,
                role=component.role,
                group=factor_group(component.factor, component.role),
                weight=component.weight,
                description=description,
            )
        )
    return factors


def _make_item(record: PerturbedGraphTextRecord, inventory: PredicateDecompositionSet) -> LLMProbeItem | None:
    edge = _first_edge(record)
    if edge is None:
        return None
    labels = _node_labels(record)
    predicate = str(edge.get("pred", ""))
    factors = _factors_for_predicate(inventory, predicate)
    if not factors:
        return None
    subj_id = str(edge.get("subj", ""))
    obj_id = str(edge.get("obj", ""))
    item = LLMProbeItem(
        id=record.id,
        dataset=record.dataset,
        variant=record.variant,
        source_edge=ProbeEdge(
            subject=labels.get(subj_id, subj_id),
            predicate=predicate,
            object=labels.get(obj_id, obj_id),
        ),
        original_text=record.original_text,
        perturbed_text=record.text,
        factors=factors,
        expected_damage=record.expected_damage.model_dump(mode="json"),
        target_factor_groups=list(record.target_factor_groups),
        deterministic_scores=score_record(record, inventory),
        metadata={
            "original_id": record.original_id,
            "split": record.split,
            "operations": [operation.model_dump(mode="json") for operation in record.operations],
        },
    )
    return item


def _stratified_sample(items: list[LLMProbeItem], per_dataset: int, seed: int) -> list[LLMProbeItem]:
    rng = random.Random(seed)
    by_dataset_variant: dict[str, dict[str, list[LLMProbeItem]]] = defaultdict(lambda: defaultdict(list))
    for item in items:
        by_dataset_variant[item.dataset][item.variant].append(item)

    selected: list[LLMProbeItem] = []
    for dataset in sorted(by_dataset_variant):
        buckets = by_dataset_variant[dataset]
        variants = [variant for variant in _VARIANT_ORDER if buckets.get(variant)]
        if not variants:
            continue
        base = per_dataset // len(variants)
        remainder = per_dataset % len(variants)
        dataset_items: list[LLMProbeItem] = []
        for idx, variant in enumerate(variants):
            bucket = list(buckets[variant])
            rng.shuffle(bucket)
            take = base + (1 if idx < remainder else 0)
            dataset_items.extend(bucket[:take])
        if len(dataset_items) < per_dataset:
            used = {item.id for item in dataset_items}
            pool = [item for bucket in buckets.values() for item in bucket if item.id not in used]
            rng.shuffle(pool)
            dataset_items.extend(pool[: per_dataset - len(dataset_items)])
        selected.extend(dataset_items[:per_dataset])
    return selected


def item_to_prompt_payload(item: LLMProbeItem) -> dict[str, Any]:
    """Return a compact prompt payload for JSONL batch files."""

    return {
        "item_id": item.id,
        "dataset": item.dataset,
        "variant": item.variant,
        "source_edge": item.source_edge.model_dump(mode="json"),
        "original_text": item.original_text,
        "perturbed_text": item.perturbed_text,
        "factors": [factor.model_dump(mode="json") for factor in item.factors],
        "required_output_schema": {
            "item_id": item.id,
            "judge_id": "<model-or-prompt-id>",
            "decisions": [
                {
                    "factor_id": factor.id,
                    "decision": "covered|partial|absent",
                    "confidence": "0.0-1.0",
                    "evidence": "short phrase or null",
                }
                for factor in item.factors
            ],
            "notes": "optional short note",
        },
    }


def write_jsonl(path: str | Path, records: list[dict[str, Any]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")


def prepare_probe(
    inputs: list[str | Path],
    inventories: list[str | Path],
    *,
    out: str | Path,
    prompt_out: str | Path | None = None,
    per_dataset: int = 50,
    seed: int = 13,
) -> dict[str, Any]:
    inventory_by_dataset = _load_inventories(inventories)
    all_items: list[LLMProbeItem] = []
    skipped = 0
    for input_path in inputs:
        for record in _read_perturbed(input_path):
            inventory = inventory_by_dataset.get(record.dataset)
            if inventory is None:
                skipped += 1
                continue
            item = _make_item(record, inventory)
            if item is None:
                skipped += 1
            else:
                all_items.append(item)

    selected = _stratified_sample(all_items, per_dataset=per_dataset, seed=seed)
    write_jsonl(out, [item.model_dump(mode="json") for item in selected])
    if prompt_out:
        write_jsonl(prompt_out, [item_to_prompt_payload(item) for item in selected])

    by_dataset: dict[str, int] = defaultdict(int)
    by_variant: dict[str, int] = defaultdict(int)
    for item in selected:
        by_dataset[item.dataset] += 1
        by_variant[f"{item.dataset}:{item.variant}"] += 1
    report = {
        "status": "passed",
        "out": str(out),
        "prompt_out": str(prompt_out) if prompt_out else None,
        "items_available": len(all_items),
        "items_written": len(selected),
        "skipped": skipped,
        "per_dataset": per_dataset,
        "by_dataset": dict(sorted(by_dataset.items())),
        "by_dataset_variant": dict(sorted(by_variant.items())),
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", nargs="+", required=True, help="Perturbed JSONL files")
    parser.add_argument("--inventories", nargs="+", required=True, help="Factor inventory JSON files")
    parser.add_argument("--out", required=True, help="Output JSONL probe items")
    parser.add_argument("--prompt-out", default=None, help="Optional JSONL prompt payloads")
    parser.add_argument("--per-dataset", type=int, default=50, help="Probe items per dataset")
    parser.add_argument("--seed", type=int, default=13)
    args = parser.parse_args()
    report = prepare_probe(
        args.inputs,
        args.inventories,
        out=args.out,
        prompt_out=args.prompt_out,
        per_dataset=args.per_dataset,
        seed=args.seed,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
