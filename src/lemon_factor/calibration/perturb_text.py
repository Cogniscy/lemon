"""Deterministic text perturbations for metric calibration.

The perturbations are intentionally simple and reproducible. Each operator emits
an explicit manifest record so that calibration results can be audited at the
example/edge level rather than treated as an opaque synthetic dataset.
"""

from __future__ import annotations

import json
import math
import random
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from lemon_factor.coverage.text_evidence import normalize_text, text_tokens
from lemon_factor.datasets.unified_io import write_jsonl
from lemon_factor.schema.graphtext import GraphTextExample

TextNoiseType = Literal[
    "swap_object",
    "swap_predicate",
    "delete_relation_phrase",
    "entity_alias",
    "predicate_paraphrase",
    "punctuation_case_noise",
]

MEANING_DESTROYING_TEXT_NOISES = {
    "swap_object",
    "swap_predicate",
    "delete_relation_phrase",
}
MEANING_PRESERVING_TEXT_NOISES = {
    "entity_alias",
    "predicate_paraphrase",
    "punctuation_case_noise",
}

_PUNCT_RE = re.compile(r"[^\w\s,.-]+", flags=re.UNICODE)

PREDICATE_PARAPHRASES: dict[str, list[str]] = {
    "birthPlace": ["is a native of", "comes from"],
    "birthDate": ["was born on"],
    "deathPlace": ["died at"],
    "location": ["is situated in", "can be found in"],
    "country": ["is in the nation of"],
    "leader": ["is headed by"],
    "creator": ["was made by"],
    "author": ["was written by"],
    "isPartOf": ["belongs to"],
    "language": ["is written in"],
    "club": ["plays for"],
    "genre": ["belongs to the genre"],
}

WRONG_RELATION_CUES = [
    "was born in",
    "died in",
    "is located in",
    "is led by",
    "was created by",
    "belongs to",
    "plays for",
]


class TextPerturbationOperation(BaseModel):
    example_id: str
    edge_index: int | None = None
    operation: str
    original: str | None = None
    replacement: str | None = None
    changed: bool = False
    metadata: dict[str, object] = Field(default_factory=dict)


class TextPerturbationRecord(BaseModel):
    example_id: str
    noise_type: str
    noise_level: float = Field(ge=0.0, le=1.0)
    expected_direction: Literal["down", "stable"]
    original_text: str
    perturbed_text: str
    changed_edges: list[int] = Field(default_factory=list)
    operations: list[TextPerturbationOperation] = Field(default_factory=list)

    @property
    def changed(self) -> bool:
        return self.original_text != self.perturbed_text


def expected_direction_for_text_noise(noise_type: str) -> Literal["down", "stable"]:
    if noise_type in MEANING_PRESERVING_TEXT_NOISES:
        return "stable"
    return "down"


def _choose_edges(example: GraphTextExample, noise_level: float, rng: random.Random) -> list[int]:
    if noise_level <= 0.0 or not example.edges:
        return []
    selected = [idx for idx, _edge in enumerate(example.edges) if rng.random() < noise_level]
    # For high-level calibration, avoid empty destructive samples when the user
    # requests non-zero noise on a very small example.
    if not selected and noise_level >= 0.5:
        selected = [rng.randrange(len(example.edges))]
    return selected


def _case_insensitive_replace(text: str, needle: str, replacement: str, *, count: int = 1) -> tuple[str, bool]:
    if not needle.strip() or needle.strip().lower() == replacement.strip().lower():
        return text, False
    pattern = re.compile(re.escape(needle), flags=re.IGNORECASE)
    updated, replacements = pattern.subn(replacement, text, count=count)
    return updated, replacements > 0


def _label_variants(label: str) -> list[str]:
    variants = [label, label.replace("_", " "), label.replace("_", ", ")]
    if "," in label:
        variants.append(label.split(",", 1)[0].strip())
    norm = normalize_text(label)
    if norm:
        variants.append(norm)
    out: list[str] = []
    for item in variants:
        item = " ".join(str(item).split())
        if item and item not in out:
            out.append(item)
    return out


def _replace_first_label(text: str, label: str, replacement: str) -> tuple[str, str | None, bool]:
    for variant in sorted(_label_variants(label), key=len, reverse=True):
        updated, changed = _case_insensitive_replace(text, variant, replacement, count=1)
        if changed:
            return updated, variant, True
    return text, None, False


def _cue_variants(predicate: str, lexical_cues: dict[str, list[str]]) -> list[str]:
    cues = list(lexical_cues.get(predicate, []))
    normalized = normalize_text(predicate)
    if normalized:
        cues.append(normalized)
    return [cue for cue in cues if cue and cue.lower() not in {"in", "of", "by"}]


def _replace_first_cue(
    text: str,
    predicate: str,
    lexical_cues: dict[str, list[str]],
    replacement: str,
) -> tuple[str, str | None, bool]:
    for cue in sorted(_cue_variants(predicate, lexical_cues), key=len, reverse=True):
        updated, changed = _case_insensitive_replace(text, cue, replacement, count=1)
        if changed:
            return updated, cue, True
    return text, None, False


def _delete_first_cue(
    text: str,
    predicate: str,
    lexical_cues: dict[str, list[str]],
) -> tuple[str, str | None, bool]:
    for cue in sorted(_cue_variants(predicate, lexical_cues), key=len, reverse=True):
        updated, changed = _case_insensitive_replace(text, cue, " ", count=1)
        if changed:
            return " ".join(updated.split()), cue, True
    return text, None, False


def _entity_alias(label: str) -> str:
    label = label.replace("_", " ")
    if "," in label:
        alias = label.split(",", 1)[0].strip()
        if alias:
            return alias
    tokens = text_tokens(label, keep_stopwords=False)
    if len(tokens) > 1:
        return " ".join(tokens[: max(1, math.ceil(len(tokens) / 2))])
    return label.lower()


def _replacement_object_label(
    object_pool: list[str],
    original_label: str,
    rng: random.Random,
) -> str:
    candidates = [label for label in object_pool if normalize_text(label) != normalize_text(original_label)]
    if not candidates:
        return f"not {original_label}"
    return rng.choice(candidates)


def _operation(
    example_id: str,
    edge_index: int | None,
    operation: str,
    original: str | None,
    replacement: str | None,
    changed: bool,
    **metadata: object,
) -> TextPerturbationOperation:
    return TextPerturbationOperation(
        example_id=example_id,
        edge_index=edge_index,
        operation=operation,
        original=original,
        replacement=replacement,
        changed=changed,
        metadata=metadata,
    )


def perturb_text_example(
    example: GraphTextExample,
    *,
    noise_type: TextNoiseType,
    noise_level: float,
    lexical_cues: dict[str, list[str]] | None = None,
    object_pool: list[str] | None = None,
    rng: random.Random | None = None,
) -> tuple[GraphTextExample, TextPerturbationRecord]:
    lexical_cues = lexical_cues or {}
    object_pool = object_pool or []
    rng = rng or random.Random(0)
    labels = example.node_labels()
    selected_edges = _choose_edges(example, noise_level, rng)
    text = example.text
    operations: list[TextPerturbationOperation] = []
    changed_edges: list[int] = []

    if noise_type == "punctuation_case_noise" and noise_level > 0.0:
        updated = _PUNCT_RE.sub("", text).lower()
        changed = updated != text
        operations.append(_operation(example.id, None, noise_type, text, updated, changed))
        text = updated

    for edge_index in selected_edges:
        edge = example.edges[edge_index]
        changed = False
        original_fragment: str | None = None
        replacement: str | None = None

        if noise_type == "swap_object":
            original_label = labels.get(edge.obj, edge.obj)
            replacement = _replacement_object_label(object_pool, original_label, rng)
            text, original_fragment, changed = _replace_first_label(text, original_label, replacement)
        elif noise_type == "swap_predicate":
            replacement = rng.choice([cue for cue in WRONG_RELATION_CUES if cue not in _cue_variants(edge.pred, lexical_cues)])
            text, original_fragment, changed = _replace_first_cue(text, edge.pred, lexical_cues, replacement)
        elif noise_type == "delete_relation_phrase":
            text, original_fragment, changed = _delete_first_cue(text, edge.pred, lexical_cues)
            replacement = ""
        elif noise_type == "entity_alias":
            # Alias the longer endpoint first. This is treated as meaning-preserving
            # but can still stress surface metrics.
            subj_label = labels.get(edge.subj, edge.subj)
            obj_label = labels.get(edge.obj, edge.obj)
            target_label = subj_label if len(subj_label) >= len(obj_label) else obj_label
            replacement = _entity_alias(target_label)
            text, original_fragment, changed = _replace_first_label(text, target_label, replacement)
        elif noise_type == "predicate_paraphrase":
            paraphrases = PREDICATE_PARAPHRASES.get(edge.pred, [])
            if not paraphrases:
                base = normalize_text(edge.pred)
                paraphrases = [f"has relation {base}" if base else "is related to"]
            replacement = rng.choice(paraphrases)
            text, original_fragment, changed = _replace_first_cue(text, edge.pred, lexical_cues, replacement)
        elif noise_type == "punctuation_case_noise":
            # Already applied once for the full example.
            continue
        else:  # pragma: no cover - guarded by Literal/CLI choices
            raise ValueError(f"Unsupported text noise type: {noise_type}")

        operations.append(
            _operation(
                example.id,
                edge_index,
                noise_type,
                original_fragment,
                replacement,
                changed,
                predicate=edge.pred,
            )
        )
        if changed:
            changed_edges.append(edge_index)

    perturbed = example.model_copy(deep=True)
    perturbed.text = text
    perturbed.metadata = dict(perturbed.metadata)
    perturbed.metadata["calibration_noise"] = {
        "noise_type": noise_type,
        "noise_level": noise_level,
        "expected_direction": expected_direction_for_text_noise(noise_type),
        "changed_edges": changed_edges,
    }
    record = TextPerturbationRecord(
        example_id=example.id,
        noise_type=noise_type,
        noise_level=noise_level,
        expected_direction=expected_direction_for_text_noise(noise_type),
        original_text=example.text,
        perturbed_text=text,
        changed_edges=changed_edges,
        operations=operations,
    )
    return perturbed, record


def perturb_text_corpus(
    examples: list[GraphTextExample],
    *,
    noise_type: TextNoiseType,
    noise_level: float,
    lexical_cues: dict[str, list[str]] | None = None,
    seed: int = 42,
) -> tuple[list[GraphTextExample], list[TextPerturbationRecord]]:
    rng = random.Random(seed)
    object_pool = [example.node_labels().get(edge.obj, edge.obj) for example in examples for edge in example.edges]
    perturbed: list[GraphTextExample] = []
    records: list[TextPerturbationRecord] = []
    for example in examples:
        item, record = perturb_text_example(
            example,
            noise_type=noise_type,
            noise_level=noise_level,
            lexical_cues=lexical_cues,
            object_pool=object_pool,
            rng=rng,
        )
        perturbed.append(item)
        records.append(record)
    return perturbed, records


def write_text_perturbation_artifacts(
    examples: list[GraphTextExample],
    records: list[TextPerturbationRecord],
    *,
    examples_out: str | Path,
    manifest_out: str | Path,
) -> None:
    write_jsonl(examples_out, examples)
    manifest_path = Path(manifest_out)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record.model_dump(mode="json"), ensure_ascii=False) + "\n")


def count_effective_text_operations(records: list[TextPerturbationRecord]) -> int:
    return sum(1 for record in records for operation in record.operations if operation.changed)
