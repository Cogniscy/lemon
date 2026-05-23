"""Common helpers for biomedical GraphText converters."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from lemon_factor.schema.graphtext import Edge, Fact, GraphTextExample, Node, Split


@dataclass
class BioEntity:
    """Minimal biomedical entity annotation."""

    id: str
    label: str
    type: str
    external_id: str | None = None
    aliases: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BioRelation:
    """Minimal biomedical relation annotation."""

    id: str
    subj: str
    pred: str
    obj: str
    evidence: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BioDocument:
    """Intermediate document representation shared by converters."""

    id: str
    split: str
    title: str = ""
    abstract: str = ""
    entities: list[BioEntity] = field(default_factory=list)
    relations: list[BioRelation] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def as_split(split: str) -> Split:
    value = split.lower()
    if value in {"validation", "valid", "dev"}:
        return Split.dev
    if value in {"train", "training"}:
        return Split.train
    if value in {"test", "testing"}:
        return Split.test
    return Split.pilot


def normalize_entity_id(value: str | None, *, prefix: str, fallback: str) -> str:
    """Normalize biomedical entity identifiers into stable GraphText node ids."""

    raw = (value or "").strip()
    if not raw or raw == "-":
        raw = fallback
    raw = raw.replace("|", "_").replace(":", "_").replace(" ", "_")
    raw = re.sub(r"[^A-Za-z0-9_.-]+", "_", raw).strip("_")
    if not raw:
        raw = re.sub(r"\W+", "_", fallback).strip("_") or "entity"
    if raw.lower().startswith(prefix.lower() + "_"):
        return raw
    return f"{prefix}_{raw}"


def make_biomedical_node(entity: BioEntity) -> Node:
    external_ids: dict[str, str] = {}
    if entity.external_id:
        if entity.external_id.upper().startswith("MESH"):
            external_ids["mesh"] = entity.external_id
        elif entity.external_id.upper().startswith("NCBI"):
            external_ids["ncbi"] = entity.external_id
        else:
            external_ids["source"] = entity.external_id
    return Node(
        id=entity.id,
        label=entity.label,
        type=entity.type,
        aliases=entity.aliases,
        external_ids=external_ids,
        metadata=entity.metadata,
    )


def make_biomedical_edge(relation: BioRelation) -> Edge:
    return Edge(
        subj=relation.subj,
        pred=relation.pred,
        obj=relation.obj,
        evidence=relation.evidence,
        metadata=relation.metadata,
    )


def make_fact(dataset: str, doc_id: str, edge_index: int, edge: Edge, nodes: dict[str, Node]) -> Fact:
    subj = nodes[edge.subj].label
    obj = nodes[edge.obj].label
    readable_pred = edge.pred.replace("_", " ")
    return Fact(
        id=f"{dataset}::{doc_id}::edge-{edge_index}",
        text=f"{subj} -- {readable_pred} -- {obj}",
        source="gold",
        edge_refs=[edge_index],
        metadata={"dataset": dataset, "predicate": edge.pred},
    )


def sentence_or_abstract_text(title: str = "", abstract: str = "") -> str:
    title = title.strip()
    abstract = abstract.strip()
    if title and abstract:
        return f"{title} {abstract}"
    return title or abstract


def document_to_graphtext(document: BioDocument, *, dataset: str) -> GraphTextExample:
    """Convert an intermediate biomedical document into GraphText."""

    # Preserve first occurrence if duplicate external IDs are present.
    nodes_by_id: dict[str, Node] = {}
    for entity in document.entities:
        nodes_by_id.setdefault(entity.id, make_biomedical_node(entity))

    edges: list[Edge] = []
    for relation in document.relations:
        if relation.subj not in nodes_by_id or relation.obj not in nodes_by_id:
            continue
        edges.append(make_biomedical_edge(relation))

    nodes = list(nodes_by_id.values())
    facts = [make_fact(dataset, document.id, idx, edge, nodes_by_id) for idx, edge in enumerate(edges)]
    return GraphTextExample(
        id=f"{dataset}::{document.split}::{document.id}",
        dataset=dataset,
        split=as_split(document.split),
        text=sentence_or_abstract_text(document.title, document.abstract),
        language="en",
        nodes=nodes,
        edges=edges,
        facts=facts,
        metadata={
            "pmid": document.id,
            "document_level": bool(
                document.metadata.get(
                    "document_level",
                    any(edge.metadata.get("document_level") is True for edge in edges),
                )
            ),
            "source_dataset": dataset,
            **document.metadata,
        },
    )


def write_manifest(
    path: str | Path,
    *,
    dataset: str,
    source: str,
    status: str,
    splits: dict[str, int],
    records: int,
    notes: list[str] | None = None,
    source_url: str | None = None,
    license_note: str | None = None,
    limitations: list[str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "dataset": dataset,
        "source": source,
        "source_url": source_url,
        "license_note": license_note,
        "status": status,
        "conversion_timestamp": now_utc_iso(),
        "records": records,
        "splits": splits,
        "notes": notes or [],
        "limitations": limitations or [],
    }
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def read_json_records(path: str | Path) -> list[dict[str, Any]]:
    """Read JSON or JSONL records from a local fixture/raw file."""

    p = Path(path)
    text = p.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if p.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    data = json.loads(text)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "documents" in data:
        return list(data["documents"])
    if isinstance(data, dict) and "records" in data:
        return list(data["records"])
    if isinstance(data, dict):
        return [data]
    raise ValueError(f"Unsupported JSON payload in {path}")


def missing_raw_dir_message(raw_dir: str | Path, *, dataset: str, source_hint: str | None = None) -> str:
    base = Path(raw_dir)
    hint = source_hint or f"Create it and place {dataset} raw files there."
    return (
        f"Raw directory does not exist: {base}.\n"
        f"Create it with: mkdir {base}\n"
        f"Then {hint}"
    )


def no_raw_files_message(raw_dir: str | Path, *, dataset: str, expected: str, source_hint: str | None = None) -> str:
    base = Path(raw_dir)
    hint = source_hint or f"Place {dataset} raw files there."
    return f"No {dataset} raw files found in {base}. Expected: {expected}. {hint}"


def choose_local_files(raw_dir: str | Path, patterns: Iterable[str]) -> list[Path]:
    base = Path(raw_dir)
    if not base.exists():
        raise FileNotFoundError(f"Raw directory does not exist: {base}")
    files: list[Path] = []
    for pattern in patterns:
        # Search recursively so direct-download repository archives and nested
        # corpus zip extractions can be passed as a single raw directory.
        files.extend(sorted(base.rglob(pattern)))
    return sorted(set(files))


def infer_split_from_name(path: str | Path) -> str:
    name = Path(path).name.lower()
    if any(token in name for token in ["train", "training"]):
        return "train"
    if any(token in name for token in ["dev", "valid", "validation", "development"]):
        return "dev"
    if "test" in name:
        return "test"
    return "pilot"


def group_documents_by_split(documents: Iterable[BioDocument]) -> dict[str, list[BioDocument]]:
    grouped: dict[str, list[BioDocument]] = defaultdict(list)
    for document in documents:
        grouped[as_split(document.split).value].append(document)
    return dict(grouped)


def write_graphtext_splits(
    out_dir: str | Path,
    *,
    dataset: str,
    documents: Iterable[BioDocument],
    limit: int | None = None,
) -> dict[str, str]:
    from lemon_factor.datasets.unified_io import write_jsonl

    grouped = group_documents_by_split(documents)
    outputs: dict[str, str] = {}
    out_base = Path(out_dir)
    out_base.mkdir(parents=True, exist_ok=True)
    for split, docs in sorted(grouped.items()):
        selected_docs = docs[:limit] if limit is not None else docs
        examples = [document_to_graphtext(doc, dataset=dataset) for doc in selected_docs]
        path = out_base / f"{dataset}_{split}.jsonl"
        write_jsonl(path, examples)
        outputs[split] = str(path)
    return outputs


def json_records_to_documents(
    records: Iterable[dict[str, Any]],
    *,
    dataset: str,
    default_split: str,
    relation_mapper: Any,
    entity_type_mapper: Any | None = None,
) -> list[BioDocument]:
    """Convert simple JSON records into intermediate documents.

    Expected record shape is intentionally permissive:
    {pmid/id, title, abstract/text, entities:[...], relations:[...]}.
    """

    documents: list[BioDocument] = []
    for idx, record in enumerate(records):
        doc_id = str(record.get("pmid") or record.get("id") or record.get("doc_id") or idx)
        split = str(record.get("split") or default_split)
        entities: list[BioEntity] = []
        raw_entities = record.get("entities", []) or record.get("annotations", [])
        for ent_idx, raw_entity in enumerate(raw_entities):
            raw_type = str(raw_entity.get("type") or raw_entity.get("entity_type") or raw_entity.get("kind") or "Entity")
            ent_type = entity_type_mapper(raw_type) if entity_type_mapper else raw_type
            label = str(raw_entity.get("text") or raw_entity.get("label") or raw_entity.get("mention") or raw_entity.get("name") or raw_entity.get("id") or f"entity-{ent_idx}")
            external_id = raw_entity.get("external_id") or raw_entity.get("normalized_id") or raw_entity.get("mesh_id") or raw_entity.get("identifier")
            entity_id = normalize_entity_id(
                str(raw_entity.get("id") or raw_entity.get("entity_id") or external_id or label),
                prefix=dataset,
                fallback=f"{doc_id}_{ent_idx}_{label}",
            )
            entities.append(
                BioEntity(
                    id=entity_id,
                    label=label,
                    type=ent_type,
                    external_id=str(external_id) if external_id else None,
                    aliases=list(raw_entity.get("aliases", []) or []),
                    metadata={"source_entity_id": raw_entity.get("id") or raw_entity.get("entity_id")},
                )
            )
        id_lookup = {
            str(raw_entity.get("id") or raw_entity.get("entity_id") or raw_entity.get("external_id") or raw_entity.get("mesh_id") or raw_entity.get("text") or raw_entity.get("label")): entity.id
            for raw_entity, entity in zip(raw_entities, entities, strict=False)
        }
        relations: list[BioRelation] = []
        for rel_idx, raw_relation in enumerate(record.get("relations", []) or []):
            raw_pred = str(raw_relation.get("type") or raw_relation.get("relation_type") or raw_relation.get("predicate") or raw_relation.get("label") or "related_to")
            pred = relation_mapper(raw_pred)
            subj_raw = str(raw_relation.get("subj") or raw_relation.get("subject") or raw_relation.get("arg1") or raw_relation.get("chemical") or raw_relation.get("source") or "")
            obj_raw = str(raw_relation.get("obj") or raw_relation.get("object") or raw_relation.get("arg2") or raw_relation.get("disease") or raw_relation.get("protein") or raw_relation.get("target") or "")
            subj = id_lookup.get(subj_raw, normalize_entity_id(subj_raw, prefix=dataset, fallback=f"{doc_id}_subj_{rel_idx}"))
            obj = id_lookup.get(obj_raw, normalize_entity_id(obj_raw, prefix=dataset, fallback=f"{doc_id}_obj_{rel_idx}"))
            relations.append(
                BioRelation(
                    id=f"{doc_id}::rel-{rel_idx}",
                    subj=subj,
                    pred=pred,
                    obj=obj,
                    evidence=raw_relation.get("evidence"),
                    metadata={
                        "dataset": dataset,
                        "raw_relation_type": raw_pred,
                        "document_level": bool(raw_relation.get("document_level", True)),
                    },
                )
            )
        title = str(record.get("title") or "")
        abstract = str(record.get("abstract") or record.get("text") or "")
        documents.append(
            BioDocument(
                id=doc_id,
                split=split,
                title=title,
                abstract=abstract,
                entities=entities,
                relations=relations,
                metadata={"source_record_index": idx},
            )
        )
    return documents
