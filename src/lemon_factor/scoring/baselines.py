"""Deterministic baseline metrics for LEM-05 perturbation scoring.

The metrics in this module are deliberately lightweight. They are not intended
as complete replacements for FactSpotter, KGGen/MINE, or LLM-based LEMON
judging. They provide reproducible, local baselines over controlled
perturbation files so that the paper can compare surface/entity signals with
factor-aware damage profiles.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable

from lemon_factor.factors.decomposition import PredicateDecompositionSet
from lemon_factor.perturbations.schema import PerturbedGraphTextRecord


@dataclass(frozen=True)
class EdgeScore:
    """Per-edge deterministic scoring signals."""

    entity_pair_recall: float
    label_match: float
    triple_match: float
    lemon_label_only: float
    lemon_full: float


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
    "chemical_inhibits_gene_or_protein": [
        "inhibits",
        "inhibited",
        "inhibition",
        "inhibitor",
        "suppresses",
        "suppressed",
    ],
    "chemical_activates_gene_or_protein": [
        "activates",
        "activated",
        "activation",
        "activator",
        "stimulates",
        "stimulated",
    ],
    "chemical_indirectly_upregulates_gene_or_protein": [
        "upregulates",
        "up-regulates",
        "increases",
        "induces",
        "enhances",
    ],
    "chemical_indirectly_downregulates_gene_or_protein": [
        "downregulates",
        "down-regulates",
        "decreases",
        "reduces",
        "represses",
    ],
    "chemical_antagonist_of_gene_or_protein": ["antagonist", "antagonizes", "blocks", "blocked"],
    "chemical_agonist_of_gene_or_protein": ["agonist", "agonizes"],
    "chemical_agonist_activator_of_gene_or_protein": ["agonist", "activator", "activates"],
    "chemical_agonist_inhibitor_of_gene_or_protein": ["agonist", "inhibitor", "inhibits"],
    "chemical_directly_regulates_gene_or_protein": ["regulates", "regulated", "modulates", "controls"],
    "direct_regulator": ["regulates", "regulated", "modulates", "controls"],
    "chemical_substrate_of_gene_or_protein": ["substrate", "substrates", "metabolized by"],
    "chemical_product_of_gene_or_protein": ["product", "produced by", "metabolite"],
    "chemical_substrate_product_of_gene_or_protein": ["substrate", "product"],
    "part_of_relation": ["part of", "component of", "subunit"],
    "chemical_disease_interaction": [
        "induced",
        "induces",
        "caused",
        "causes",
        "associated with",
        "resulted in",
        "due to",
        "toxicity",
    ],
}

# Variant-specific factor damage. These values are used only for the deterministic
# LEMON-full proxy in perturbation scoring. LLM adjudication is handled in a later
# patch and should not be confused with this proxy.
_TARGET_TO_GROUPS: dict[str, set[str]] = {
    "entity_presence": {"entity_presence", "participant_roles"},
    "participant_roles": {"participant_roles", "entity_presence"},
    "predicate_meaning": {"predicate_meaning", "predicate_specificity", "evidence_form"},
    "predicate_specificity": {"predicate_specificity", "predicate_meaning", "evidence_form"},
    "directionality": {"directionality", "participant_roles"},
    "polarity": {"polarity", "predicate_meaning"},
    "evidence_form": {"evidence_form", "predicate_meaning", "predicate_specificity"},
}


def normalize_text(text: str) -> str:
    """Normalize text for coarse lexical matching."""

    return re.sub(r"\s+", " ", text.casefold()).strip()


def normalize_label(label: str) -> str:
    """Normalize a node label or predicate cue."""

    label = label.replace("_", " ").replace("/", " ")
    label = re.sub(r"(?<!^)([A-Z])", r" \1", label)
    return normalize_text(label)


def _contains_phrase(text_norm: str, phrase: str) -> bool:
    phrase_norm = normalize_label(phrase)
    if not phrase_norm:
        return False
    # Word-boundary matching is too brittle for biomedical names with symbols.
    return phrase_norm in text_norm


def _label_variants(label: str) -> list[str]:
    raw = [label, label.replace("_", " ")]
    if "," in label:
        raw.append(label.split(",", 1)[0].strip())
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        item = " ".join(item.split())
        key = item.casefold()
        if item and key not in seen:
            seen.add(key)
            out.append(item)
    return sorted(out, key=len, reverse=True)


def node_present(text: str, label: str) -> bool:
    """Return whether at least one label variant appears in text."""

    text_norm = normalize_text(text)
    return any(_contains_phrase(text_norm, variant) for variant in _label_variants(label))


def _predicate_surface_forms(predicate: str) -> list[str]:
    spaced = re.sub(r"(?<!^)([A-Z])", r" \1", predicate).replace("_", " ").replace("/", " ")
    compact = re.sub(r"[_/]+", " ", predicate)
    forms = [predicate, spaced, compact, spaced.lower()]
    for cue in _GENERIC_CUES.get(predicate, []):
        forms.append(cue)
    clean: list[str] = []
    seen: set[str] = set()
    for form in forms:
        form = " ".join(str(form).split())
        key = form.casefold()
        if len(form) >= 3 and key not in seen:
            seen.add(key)
            clean.append(form)
    return sorted(clean, key=len, reverse=True)


def predicate_match(text: str, predicate: str) -> float:
    """Return a coarse binary predicate-label/cue match."""

    text_norm = normalize_text(text)
    return 1.0 if any(_contains_phrase(text_norm, cue) for cue in _predicate_surface_forms(predicate)) else 0.0


def _safe_mean(values: Iterable[float]) -> float:
    values = list(values)
    if not values:
        return 0.0
    return sum(values) / len(values)


def _harmonic(left: float, right: float) -> float:
    if left <= 0 or right <= 0:
        return 0.0
    return 2 * left * right / (left + right)


def _node_labels_by_id(record: PerturbedGraphTextRecord) -> dict[str, str]:
    return {node.get("id", ""): node.get("label", "") for node in record.nodes if node.get("id")}


def _component_group(factor_id: str, role: str) -> str:
    """Map a factor component to a coarse perturbation-sensitive group."""

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


def _target_groups(record: PerturbedGraphTextRecord) -> set[str]:
    groups: set[str] = set()
    for target in record.target_factor_groups:
        groups.add(target)
        groups.update(_TARGET_TO_GROUPS.get(target, set()))
    return groups


def _changed(record: PerturbedGraphTextRecord) -> bool:
    return any(operation.changed for operation in record.operations)


def _lemon_full_proxy(
    record: PerturbedGraphTextRecord,
    edge_predicate: str,
    inventory: PredicateDecompositionSet,
) -> float:
    """Deterministic factor score used for perturbation baselines.

    The score uses the fixed inventory and the perturbation metadata. It is a
    proxy for the expected factor damage, not an LLM or human judgment.
    """

    decomposition = inventory.decompositions.get(edge_predicate)
    if decomposition is None:
        return 0.0
    if not _changed(record):
        return 1.0
    damaged = _target_groups(record)
    retained = 0.0
    for component in decomposition.components:
        group = _component_group(component.factor, component.role)
        if group not in damaged:
            retained += component.weight
    return max(0.0, min(1.0, retained))


def score_edge(
    record: PerturbedGraphTextRecord,
    edge: dict[str, Any],
    labels: dict[str, str],
    inventory: PredicateDecompositionSet,
) -> EdgeScore:
    """Score one source edge against the perturbed text."""

    subj_label = labels.get(edge.get("subj", ""), edge.get("subj", ""))
    obj_label = labels.get(edge.get("obj", ""), edge.get("obj", ""))
    subj_present = node_present(record.text, subj_label)
    obj_present = node_present(record.text, obj_label)
    entity_pair_recall = (float(subj_present) + float(obj_present)) / 2.0
    pred = str(edge.get("pred", ""))
    label = predicate_match(record.text, pred)
    triple = 1.0 if subj_present and obj_present and label > 0.0 else 0.0
    lemon_full = _lemon_full_proxy(record, pred, inventory)
    return EdgeScore(
        entity_pair_recall=entity_pair_recall,
        label_match=label,
        triple_match=triple,
        lemon_label_only=label,
        lemon_full=lemon_full,
    )


def _entity_recall(record: PerturbedGraphTextRecord) -> float:
    labels = _node_labels_by_id(record)
    endpoint_ids = {edge.get("subj") for edge in record.edges} | {edge.get("obj") for edge in record.edges}
    endpoint_labels = [labels[node_id] for node_id in endpoint_ids if node_id in labels]
    if not endpoint_labels:
        return 0.0
    return _safe_mean(float(node_present(record.text, label)) for label in endpoint_labels)


def _entity_jaccard(record: PerturbedGraphTextRecord) -> float:
    labels = _node_labels_by_id(record)
    endpoint_ids = {edge.get("subj") for edge in record.edges} | {edge.get("obj") for edge in record.edges}
    if not endpoint_ids:
        return 0.0
    original_present = {
        node_id for node_id in endpoint_ids if node_id in labels and node_present(record.original_text, labels[node_id])
    }
    current_present = {
        node_id for node_id in endpoint_ids if node_id in labels and node_present(record.text, labels[node_id])
    }
    union = original_present | current_present
    if not union:
        return 0.0
    return len(original_present & current_present) / len(union)


def score_record(
    record: PerturbedGraphTextRecord,
    inventory: PredicateDecompositionSet,
) -> dict[str, float]:
    """Return deterministic baseline scores for one perturbed record."""

    labels = _node_labels_by_id(record)
    edge_scores = [score_edge(record, edge, labels, inventory) for edge in record.edges]
    entity_recall = _entity_recall(record)
    label_match = _safe_mean(score.label_match for score in edge_scores)
    triple_match = _safe_mean(score.triple_match for score in edge_scores)
    mine_node = entity_recall
    mine_edge = triple_match
    mine_style = _harmonic(mine_node, mine_edge)
    lemon_label_only = _safe_mean(score.lemon_label_only for score in edge_scores)
    lemon_full = _safe_mean(score.lemon_full for score in edge_scores)
    return {
        "entity_recall": round(entity_recall, 6),
        "entity_jaccard": round(_entity_jaccard(record), 6),
        "label_match": round(label_match, 6),
        "triple_match": round(triple_match, 6),
        "mine_node": round(mine_node, 6),
        "mine_edge": round(mine_edge, 6),
        "mine_style": round(mine_style, 6),
        "lemon_label_only": round(lemon_label_only, 6),
        "lemon_full": round(lemon_full, 6),
    }
