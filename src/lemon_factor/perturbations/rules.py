"""Deterministic perturbation rules for graph-text evaluation.

The rules are intentionally simple and auditable. They do not try to create
fluent counterfactual biomedical abstracts; they create controlled edits that
stress one semantic factor group at a time while preserving the original graph.
"""

from __future__ import annotations

import re
from typing import Any

from lemon_factor.perturbations.schema import ExpectedDamage, PerturbationOperation, PerturbationVariant
from lemon_factor.schema.graphtext import Edge, GraphTextExample

_FACTOR_GROUPS: dict[str, list[str]] = {
    "node_deletion": ["entity_presence", "participant_roles"],
    "edge_deletion": ["predicate_meaning", "evidence_form"],
    "argument_swap": ["directionality", "participant_roles"],
    "polarity_flip": ["polarity", "predicate_meaning"],
    "relation_blur": ["predicate_specificity", "evidence_form"],
}

_EXPECTED_DAMAGE: dict[str, ExpectedDamage] = {
    "node_deletion": ExpectedDamage(
        direction="down",
        severity="high",
        rationale="Removing an entity mention should reduce node and role evidence.",
    ),
    "edge_deletion": ExpectedDamage(
        direction="down",
        severity="high",
        rationale="Removing a relation cue should preserve entities but weaken predicate evidence.",
    ),
    "argument_swap": ExpectedDamage(
        direction="down",
        severity="high",
        rationale="Swapping arguments should damage role assignment and directionality.",
    ),
    "polarity_flip": ExpectedDamage(
        direction="down",
        severity="high",
        rationale="Replacing a positive/negative cue should damage the polarity factor.",
    ),
    "relation_blur": ExpectedDamage(
        direction="down",
        severity="medium",
        rationale="Replacing a specific relation cue with a broad cue should reduce predicate specificity.",
    ),
}

_GENERIC_CUES: dict[str, list[str]] = {
    "birthPlace": ["was born in", "born in", "birthplace", "birth place"],
    "birthDate": ["was born on", "born on", "birth date"],
    "deathPlace": ["died in", "died at", "death place"],
    "country": ["country", "from", "in the nation of", "is in"],
    "location": ["is located in", "located in", "is situated in", "is in"],
    "isPartOf": ["is part of", "part of", "belongs to"],
    "leader": ["is led by", "led by", "leader"],
    "creator": ["was created by", "created by", "made by"],
    "author": ["was written by", "written by", "author"],
    "club": ["plays for", "club"],
    "language": ["language", "is written in", "spoken in"],
    "alternativeName": ["also known as", "different names include", "alternative name"],
    "chemical_inhibits_gene_or_protein": ["inhibits", "inhibited", "inhibition", "inhibitor", "suppresses", "suppressed"],
    "chemical_activates_gene_or_protein": ["activates", "activated", "activation", "activator", "stimulates", "stimulated"],
    "chemical_indirectly_upregulates_gene_or_protein": ["upregulates", "up-regulates", "increases", "induces", "enhances"],
    "chemical_indirectly_downregulates_gene_or_protein": ["downregulates", "down-regulates", "decreases", "reduces", "represses"],
    "chemical_antagonist_of_gene_or_protein": ["antagonist", "antagonizes", "blocks", "blocked"],
    "chemical_agonist_of_gene_or_protein": ["agonist", "agonizes"],
    "chemical_agonist_activator_of_gene_or_protein": ["agonist", "activator", "activates"],
    "chemical_directly_regulates_gene_or_protein": ["regulates", "regulated", "modulates", "controls"],
    "chemical_substrate_of_gene_or_protein": ["substrate", "substrates", "metabolized by"],
    "chemical_product_of_gene_or_protein": ["product", "produced by", "metabolite"],
    "chemical_substrate_product_of_gene_or_protein": ["substrate", "product"],
    "part_of_relation": ["part of", "component of", "subunit"],
    "chemical_disease_interaction": ["induced", "induces", "caused", "causes", "associated with", "resulted in", "due to", "toxicity"],
}

_POLARITY_REPLACEMENTS: list[tuple[str, str]] = [
    ("inhibits", "activates"),
    ("inhibited", "activated"),
    ("inhibition", "activation"),
    ("inhibitor", "activator"),
    ("suppresses", "stimulates"),
    ("suppressed", "stimulated"),
    ("activates", "inhibits"),
    ("activated", "inhibited"),
    ("activation", "inhibition"),
    ("activator", "inhibitor"),
    ("stimulates", "suppresses"),
    ("stimulated", "suppressed"),
    ("upregulates", "downregulates"),
    ("up-regulates", "down-regulates"),
    ("downregulates", "upregulates"),
    ("down-regulates", "up-regulates"),
    ("increases", "decreases"),
    ("decreases", "increases"),
    ("induces", "does not induce"),
    ("induced", "not induced"),
    ("causes", "does not cause"),
    ("caused", "not caused"),
    ("resulted in", "was not associated with"),
]


def target_factor_groups(variant: PerturbationVariant) -> list[str]:
    return list(_FACTOR_GROUPS[variant])


def expected_damage(variant: PerturbationVariant) -> ExpectedDamage:
    return _EXPECTED_DAMAGE[variant]


def _labels(example: GraphTextExample) -> dict[str, str]:
    return example.node_labels()


def _edge_label_pair(example: GraphTextExample, edge: Edge) -> tuple[str, str]:
    labels = _labels(example)
    return labels.get(edge.subj, edge.subj), labels.get(edge.obj, edge.obj)


def _label_variants(label: str) -> list[str]:
    raw = [label, label.replace("_", " ")]
    if "," in label:
        raw.append(label.split(",", 1)[0].strip())
    out: list[str] = []
    for item in raw:
        item = " ".join(item.split())
        if item and item.lower() not in {seen.lower() for seen in out}:
            out.append(item)
    return sorted(out, key=len, reverse=True)


def _replace_once(text: str, needle: str, replacement: str) -> tuple[str, bool]:
    if not needle.strip():
        return text, False
    pattern = re.compile(re.escape(needle), flags=re.IGNORECASE)
    updated, count = pattern.subn(replacement, text, count=1)
    updated = re.sub(r"\s+", " ", updated).strip()
    return updated, count > 0


def _replace_first_label(text: str, label: str, replacement: str) -> tuple[str, str | None, bool]:
    for variant in _label_variants(label):
        updated, changed = _replace_once(text, variant, replacement)
        if changed:
            return updated, variant, True
    return text, None, False


def _cue_variants(predicate: str) -> list[str]:
    cues = list(_GENERIC_CUES.get(predicate, []))
    spaced = re.sub(r"(?<!^)([A-Z])", r" \1", predicate).replace("_", " ").replace("/", " ")
    cues.extend([spaced, spaced.lower()])
    clean: list[str] = []
    for cue in cues:
        cue = " ".join(cue.split())
        if len(cue) >= 3 and cue.lower() not in {item.lower() for item in clean}:
            clean.append(cue)
    return sorted(clean, key=len, reverse=True)


def _replace_first_cue(text: str, predicate: str, replacement: str) -> tuple[str, str | None, bool]:
    for cue in _cue_variants(predicate):
        updated, changed = _replace_once(text, cue, replacement)
        if changed:
            return updated, cue, True
    return text, None, False


def _swap_two_labels(text: str, left: str, right: str) -> tuple[str, list[str], bool]:
    left_token = "__LEMON_LEFT_ARG__"
    right_token = "__LEMON_RIGHT_ARG__"
    updated, left_hit, left_changed = _replace_first_label(text, left, left_token)
    updated, right_hit, right_changed = _replace_first_label(updated, right, right_token)
    if left_changed and right_changed:
        updated = updated.replace(left_token, right).replace(right_token, left)
        return updated, [left_hit or left, right_hit or right], True
    updated = updated.replace(left_token, left).replace(right_token, right)
    return text, [item for item in [left_hit, right_hit] if item], False


def _flip_polarity(text: str) -> tuple[str, str | None, str | None, bool]:
    for source, target in sorted(_POLARITY_REPLACEMENTS, key=lambda item: len(item[0]), reverse=True):
        updated, changed = _replace_once(text, source, target)
        if changed:
            return updated, source, target, True
    return text, None, None, False


def _first_edge(example: GraphTextExample) -> tuple[int, Edge] | None:
    for idx, edge in enumerate(example.edges):
        return idx, edge
    return None


def perturb_example(example: GraphTextExample, variant: PerturbationVariant) -> tuple[str, list[PerturbationOperation]]:
    """Return perturbed text and operation records for one example."""

    selected = _first_edge(example)
    if selected is None:
        return example.text, [PerturbationOperation(operation=variant, changed=False, metadata={"reason": "no_edges"})]

    edge_index, edge = selected
    subj_label, obj_label = _edge_label_pair(example, edge)
    text = example.text

    if variant == "node_deletion":
        target = obj_label if len(obj_label) >= len(subj_label) else subj_label
        updated, matched, changed = _replace_first_label(text, target, "")
        return updated, [
            PerturbationOperation(
                edge_index=edge_index,
                operation="node_deletion",
                target=matched or target,
                replacement="",
                changed=changed,
                metadata={"predicate": edge.pred},
            )
        ]

    if variant == "edge_deletion":
        updated, matched, changed = _replace_first_cue(text, edge.pred, "")
        return updated, [
            PerturbationOperation(
                edge_index=edge_index,
                operation="edge_deletion",
                target=matched or edge.pred,
                replacement="",
                changed=changed,
                metadata={"predicate": edge.pred},
            )
        ]

    if variant == "argument_swap":
        updated, matched, changed = _swap_two_labels(text, subj_label, obj_label)
        return updated, [
            PerturbationOperation(
                edge_index=edge_index,
                operation="argument_swap",
                target=" | ".join(matched) if matched else f"{subj_label} | {obj_label}",
                replacement=f"{obj_label} | {subj_label}",
                changed=changed,
                metadata={"predicate": edge.pred},
            )
        ]

    if variant == "polarity_flip":
        updated, source, target, changed = _flip_polarity(text)
        if not changed and "chemical_disease_interaction" == edge.pred:
            updated, source, changed = _replace_first_cue(text, edge.pred, "is not clearly caused by")
            target = "is not clearly caused by" if changed else None
        return updated, [
            PerturbationOperation(
                edge_index=edge_index,
                operation="polarity_flip",
                target=source or edge.pred,
                replacement=target,
                changed=changed,
                metadata={"predicate": edge.pred},
            )
        ]

    if variant == "relation_blur":
        replacement = "is associated with" if example.dataset == "bc5cdr" else "is related to"
        if example.dataset == "drugprot":
            replacement = "affects"
        updated, matched, changed = _replace_first_cue(text, edge.pred, replacement)
        return updated, [
            PerturbationOperation(
                edge_index=edge_index,
                operation="relation_blur",
                target=matched or edge.pred,
                replacement=replacement,
                changed=changed,
                metadata={"predicate": edge.pred},
            )
        ]

    raise ValueError(f"Unsupported perturbation variant: {variant}")


def build_perturbed_record(example: GraphTextExample, variant: PerturbationVariant) -> dict[str, Any]:
    text, operations = perturb_example(example, variant)
    if not text.strip():
        text = example.text
        operations.append(
            PerturbationOperation(
                operation="restore_empty_text",
                changed=True,
                metadata={"reason": "operator_would_empty_text"},
            )
        )
    metadata = dict(example.metadata)
    metadata["perturbation"] = {
        "original_id": example.id,
        "variant": variant,
        "expected_damage": expected_damage(variant).model_dump(mode="json"),
        "target_factor_groups": target_factor_groups(variant),
        "changed": any(operation.changed for operation in operations),
    }
    return {
        "id": f"{example.id}::perturb::{variant}",
        "original_id": example.id,
        "dataset": example.dataset,
        "split": example.split.value if hasattr(example.split, "value") else str(example.split),
        "variant": variant,
        "text": text,
        "original_text": example.text,
        "language": example.language,
        "nodes": [node.model_dump(mode="json") for node in example.nodes],
        "edges": [edge.model_dump(mode="json") for edge in example.edges],
        "facts": [fact.model_dump(mode="json") for fact in example.facts],
        "expected_damage": expected_damage(variant).model_dump(mode="json"),
        "target_factor_groups": target_factor_groups(variant),
        "operations": [operation.model_dump(mode="json") for operation in operations],
        "metadata": metadata,
    }
