"""Convert BC5CDR chemical--disease relation data to GraphText JSONL.

Supported inputs:
- local PubTator files under --raw-dir;
- simple JSON/JSONL fixtures with entities and relations;
- HuggingFace converted Parquet files via --source hf-parquet;
- legacy alias --source bigbio, which now routes to hf-parquet.
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from lemon_factor.datasets.biomedical_download import (
    DownloadError,
    download_github_repo_zip,
    extract_nested_zips,
    write_acquisition_manifest,
)
from lemon_factor.datasets.biomedical_common import (
    BioDocument,
    BioEntity,
    BioRelation,
    choose_local_files,
    infer_split_from_name,
    json_records_to_documents,
    missing_raw_dir_message,
    no_raw_files_message,
    normalize_entity_id,
    read_json_records,
    write_graphtext_splits,
    write_manifest,
)

DATASET = "bc5cdr"
SOURCE_URL = "https://www.ncbi.nlm.nih.gov/research/bionlp/Data/"
DIRECT_SOURCE_URL = "https://github.com/openbiocorpora/biocreative-v-cdr"
LICENSE_NOTE = "BC5CDR is distributed by NCBI/BioCreative; verify current access and license terms before redistribution."


def map_bc5cdr_relation(raw: str) -> str:
    value = raw.strip().upper()
    if value in {"CID", "CHEMICAL_DISEASE_INTERACTION", "CDR"}:
        return "chemical_disease_interaction"
    return raw.strip().lower().replace("-", "_").replace(" ", "_")


def map_bc5cdr_entity_type(raw: str) -> str:
    value = raw.strip().lower()
    if value == "chemical":
        return "Chemical"
    if value == "disease":
        return "Disease"
    return raw.strip() or "Entity"


def parse_pubtator_files(paths: list[Path]) -> list[BioDocument]:
    documents: list[BioDocument] = []
    for path in paths:
        split = infer_split_from_name(path)
        text = path.read_text(encoding="utf-8").splitlines()
        current: dict[str, Any] | None = None
        entities: list[BioEntity] = []
        relations: list[BioRelation] = []

        def flush() -> None:
            nonlocal current, entities, relations
            if current is None:
                return
            documents.append(
                BioDocument(
                    id=current["pmid"],
                    split=split,
                    title=current.get("title", ""),
                    abstract=current.get("abstract", ""),
                    entities=entities,
                    relations=relations,
                    metadata={"source_file": str(path), "source_format": "pubtator"},
                )
            )
            current = None
            entities = []
            relations = []

        for line in text + [""]:
            stripped = line.strip()
            if not stripped:
                flush()
                continue
            if "|t|" in stripped:
                flush()
                pmid, title = stripped.split("|t|", 1)
                current = {"pmid": pmid, "title": title, "abstract": ""}
                continue
            if "|a|" in stripped:
                pmid, abstract = stripped.split("|a|", 1)
                if current is None:
                    current = {"pmid": pmid, "title": "", "abstract": abstract}
                else:
                    current["abstract"] = abstract
                continue
            parts = stripped.split("\t")
            if len(parts) >= 6 and current is not None:
                pmid, start, end, mention, ent_type, external_id = parts[:6]
                ent_id = normalize_entity_id(
                    external_id,
                    prefix=DATASET,
                    fallback=f"{pmid}_{start}_{end}_{mention}",
                )
                entities.append(
                    BioEntity(
                        id=ent_id,
                        label=mention,
                        type=map_bc5cdr_entity_type(ent_type),
                        external_id=external_id,
                        metadata={"start": int(start), "end": int(end), "source_file": str(path)},
                    )
                )
                continue
            if len(parts) >= 4 and current is not None:
                pmid, relation_type, chemical_id, disease_id = parts[:4]
                relations.append(
                    BioRelation(
                        id=f"{pmid}::CID::{len(relations)}",
                        subj=normalize_entity_id(chemical_id, prefix=DATASET, fallback=f"{pmid}_chemical"),
                        pred=map_bc5cdr_relation(relation_type),
                        obj=normalize_entity_id(disease_id, prefix=DATASET, fallback=f"{pmid}_disease"),
                        metadata={
                            "dataset": DATASET,
                            "raw_relation_type": relation_type,
                            "source_file": str(path),
                            "document_level": True,
                        },
                    )
                )
        
    return documents


def parse_bioc_xml_files(paths: list[Path]) -> list[BioDocument]:
    """Parse a small, permissive subset of BioC XML used by BC5CDR dumps."""

    documents: list[BioDocument] = []
    for path in paths:
        split = infer_split_from_name(path)
        root = ET.parse(path).getroot()
        for doc_el in root.findall(".//document"):
            pmid = (doc_el.findtext("id") or path.stem).strip()
            title = ""
            abstract_parts: list[str] = []
            entities: list[BioEntity] = []
            source_ann_to_node: dict[str, str] = {}

            for passage in doc_el.findall("passage"):
                ptype = ""
                for infon in passage.findall("infon"):
                    if infon.attrib.get("key", "").lower() == "type":
                        ptype = (infon.text or "").strip().lower()
                text = (passage.findtext("text") or "").strip()
                if text:
                    if ptype == "title" and not title:
                        title = text
                    else:
                        abstract_parts.append(text)
                for ann_idx, annotation in enumerate(passage.findall("annotation")):
                    ann_id = annotation.attrib.get("id") or annotation.findtext("id") or f"{pmid}_ann_{len(entities)}"
                    ent_type = "Entity"
                    external_id = None
                    for infon in annotation.findall("infon"):
                        key = infon.attrib.get("key", "").lower()
                        value = (infon.text or "").strip()
                        if key == "type":
                            ent_type = value
                        elif key in {"mesh", "identifier", "normalized", "db_id"}:
                            external_id = value
                    mention = (annotation.findtext("text") or ann_id).strip()
                    loc = annotation.find("location")
                    start = int(loc.attrib.get("offset", 0)) if loc is not None else None
                    length = int(loc.attrib.get("length", 0)) if loc is not None else None
                    ent_id = normalize_entity_id(external_id or ann_id, prefix=DATASET, fallback=f"{pmid}_{ann_idx}_{mention}")
                    source_ann_to_node[str(ann_id)] = ent_id
                    entities.append(
                        BioEntity(
                            id=ent_id,
                            label=mention,
                            type=map_bc5cdr_entity_type(ent_type),
                            external_id=external_id,
                            metadata={"source_annotation_id": ann_id, "start": start, "length": length, "source_file": str(path)},
                        )
                    )

            relations: list[BioRelation] = []
            for rel_idx, relation in enumerate(doc_el.findall("relation")):
                rel_type = "CID"
                for infon in relation.findall("infon"):
                    if infon.attrib.get("key", "").lower() == "type":
                        rel_type = (infon.text or "CID").strip()
                node_refs = [node.attrib.get("refid") for node in relation.findall("node") if node.attrib.get("refid")]
                if len(node_refs) < 2:
                    continue
                subj = source_ann_to_node.get(str(node_refs[0]), normalize_entity_id(str(node_refs[0]), prefix=DATASET, fallback=f"{pmid}_arg1"))
                obj = source_ann_to_node.get(str(node_refs[1]), normalize_entity_id(str(node_refs[1]), prefix=DATASET, fallback=f"{pmid}_arg2"))
                relations.append(
                    BioRelation(
                        id=f"{pmid}::{rel_type}::{rel_idx}",
                        subj=subj,
                        pred=map_bc5cdr_relation(rel_type),
                        obj=obj,
                        metadata={"dataset": DATASET, "raw_relation_type": rel_type, "source_file": str(path), "document_level": True},
                    )
                )
            documents.append(
                BioDocument(
                    id=pmid,
                    split=split,
                    title=title,
                    abstract=" ".join(abstract_parts),
                    entities=entities,
                    relations=relations,
                    metadata={"source_file": str(path), "source_format": "bioc_xml"},
                )
            )
    return documents


def load_local_documents(raw_dir: str | Path) -> list[BioDocument]:
    try:
        files = choose_local_files(raw_dir, ["*.json", "*.jsonl", "*.xml", "*.bioc", "*.BioC*", "*.PubTator*", "*.pubtator*", "*.txt"])
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            missing_raw_dir_message(
                raw_dir,
                dataset="BC5CDR",
                source_hint="place BC5CDR PubTator/BioC/JSON/JSONL files there, or run with --source hf-parquet if converted Parquet is available.",
            )
        ) from exc
    if not files:
        raise FileNotFoundError(
            no_raw_files_message(
                raw_dir,
                dataset="BC5CDR",
                expected="*.json, *.jsonl, *.xml, *.bioc, *.BioC*, *.PubTator*, *.pubtator*, or *.txt",
                source_hint="Use --source hf-parquet if you want to try HuggingFace converted Parquet instead.",
            )
        )
    documents: list[BioDocument] = []
    pubtator_files: list[Path] = []
    bioc_xml_files: list[Path] = []
    for path in files:
        suffix = path.suffix.lower()
        if suffix in {".json", ".jsonl"}:
            records = read_json_records(path)
            documents.extend(
                json_records_to_documents(
                    records,
                    dataset=DATASET,
                    default_split=infer_split_from_name(path),
                    relation_mapper=map_bc5cdr_relation,
                    entity_type_mapper=map_bc5cdr_entity_type,
                )
            )
        elif suffix in {".xml", ".bioc"} or "bioc" in path.name.lower():
            bioc_xml_files.append(path)
        else:
            pubtator_files.append(path)
    if pubtator_files:
        documents.extend(parse_pubtator_files(pubtator_files))
    if bioc_xml_files:
        documents.extend(parse_bioc_xml_files(bioc_xml_files))
    return documents


def download_direct_corpus(download_dir: str | Path, acquisition_manifest: str | Path | None = None) -> Path:
    """Download the Open Biomedical Corpora BC5CDR mirror and return raw dir."""

    out_dir = Path(download_dir)
    try:
        download_github_repo_zip("openbiocorpora", "biocreative-v-cdr", out_dir, branch="master")
        extract_nested_zips(out_dir)
    except DownloadError as exc:  # pragma: no cover - network dependent
        raise RuntimeError(
            "Could not download BC5CDR directly. Manual fallback: download the BioCreative V CDR corpus "
            f"from {DIRECT_SOURCE_URL} and place PubTator/BioC files under {out_dir}."
        ) from exc
    if acquisition_manifest:
        write_acquisition_manifest(
            acquisition_manifest,
            dataset=DATASET,
            source_type="github_repo_zip",
            source_url=DIRECT_SOURCE_URL,
            raw_dir=out_dir,
            status="downloaded",
            license_note=LICENSE_NOTE,
            notes=["Downloaded from the Open Biomedical Corpora BC5CDR mirror."],
        )
    return out_dir



HF_PARQUET_API_URL = "https://huggingface.co/api/datasets/bigbio/bc5cdr/parquet"


def _read_json_url(url: str) -> Any:
    try:
        with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310 - fixed public API URL
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:  # pragma: no cover - network dependent
        raise RuntimeError(f"Could not reach HuggingFace parquet API: {url}") from exc
    except json.JSONDecodeError as exc:  # pragma: no cover - network dependent
        raise RuntimeError(f"HuggingFace parquet API returned invalid JSON: {url}") from exc


def parquet_payload_to_data_files(payload: Any) -> dict[str, list[str]]:
    """Convert the HuggingFace /parquet response into load_dataset data_files.

    The endpoint shape can vary. We accept either a list of file objects or a
    dict with a parquet_files/files key. Each file object should contain a split
    plus either a direct url or a filename/path inside refs/convert/parquet.
    """

    if isinstance(payload, dict):
        entries = payload.get("parquet_files") or payload.get("files") or payload.get("siblings") or []
    else:
        entries = payload
    if not isinstance(entries, list):
        raise RuntimeError("Unexpected HuggingFace parquet API payload: expected a file list")

    data_files: dict[str, list[str]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        split = str(entry.get("split") or entry.get("name") or "").strip()
        if not split:
            filename_for_split = str(entry.get("filename") or entry.get("path") or "")
            parts = filename_for_split.replace("\\", "/").split("/")
            split = next((part for part in parts if part in {"train", "validation", "dev", "test"}), "")
        if split == "validation":
            split = "dev"
        if not split:
            continue

        url = entry.get("url") or entry.get("download_url")
        if not url:
            filename = str(entry.get("filename") or entry.get("path") or entry.get("rfilename") or "")
            if not filename:
                continue
            if filename.startswith(("http://", "https://", "hf://")):
                url = filename
            else:
                config = str(entry.get("config") or entry.get("config_name") or "bc5cdr_bigbio_kb")
                filename = filename.lstrip("/")
                if not filename.startswith(f"{config}/"):
                    filename = f"{config}/{split}/{Path(filename).name}"
                url = f"hf://datasets/bigbio/bc5cdr@refs/convert/parquet/{filename}"
        data_files.setdefault(split, []).append(str(url))
    if not data_files:
        raise RuntimeError(
            "No converted Parquet files were found for bigbio/bc5cdr. "
            "Use --source local with BC5CDR PubTator/BioC/JSONL files, or temporarily use datasets<4 with the legacy BigBio script."
        )
    return data_files


def _row_passage_text(passages: Any) -> tuple[str, str]:
    title = ""
    abstract_parts: list[str] = []
    if not isinstance(passages, list):
        return title, ""
    for passage in passages:
        if not isinstance(passage, dict):
            continue
        ptype = str(passage.get("type") or passage.get("section_type") or "").lower()
        text = passage.get("text")
        if isinstance(text, list):
            text = " ".join(map(str, text))
        if ptype == "title" and text:
            title = str(text)
        elif text:
            abstract_parts.append(str(text))
    return title, " ".join(abstract_parts)


def bigbio_row_to_document(row: dict[str, Any], split_name: str) -> BioDocument:
    doc_id = str(row.get("document_id") or row.get("id") or row.get("pmid") or row.get("doc_id"))
    title, abstract = _row_passage_text(row.get("passages", []) or [])
    if not title and not abstract:
        title = str(row.get("title") or "")
        abstract = str(row.get("abstract") or row.get("text") or "")

    entities: list[BioEntity] = []
    for ent_idx, entity in enumerate(row.get("entities", []) or row.get("annotations", []) or []):
        if not isinstance(entity, dict):
            continue
        label = str(entity.get("text") or entity.get("mention") or entity.get("label") or entity.get("id") or f"entity-{ent_idx}")
        raw_type = str(entity.get("type") or entity.get("entity_type") or "Entity")
        external_id = entity.get("db_id") or entity.get("normalized") or entity.get("normalized_id") or entity.get("id")
        ent_id = normalize_entity_id(str(external_id or entity.get("id") or label), prefix=DATASET, fallback=f"{doc_id}_{ent_idx}")
        entities.append(
            BioEntity(
                id=ent_id,
                label=label,
                type=map_bc5cdr_entity_type(raw_type),
                external_id=str(external_id) if external_id else None,
                metadata={"source_entity_id": entity.get("id"), "source_split": split_name},
            )
        )
    id_lookup = {str(entity.metadata.get("source_entity_id")): entity.id for entity in entities}
    relations: list[BioRelation] = []
    for rel_idx, relation in enumerate(row.get("relations", []) or []):
        if not isinstance(relation, dict):
            continue
        args = relation.get("arg_ids") or relation.get("arguments") or relation.get("args") or []
        if isinstance(args, list) and args and isinstance(args[0], dict):
            args = [arg.get("ref_id") or arg.get("id") or arg.get("entity_id") for arg in args]
        if len(args) < 2:
            subj_candidate = relation.get("subj") or relation.get("subject") or relation.get("arg1")
            obj_candidate = relation.get("obj") or relation.get("object") or relation.get("arg2")
            args = [subj_candidate, obj_candidate]
        if len(args) < 2 or args[0] is None or args[1] is None:
            continue
        subj = id_lookup.get(str(args[0]), normalize_entity_id(str(args[0]), prefix=DATASET, fallback=f"{doc_id}_arg1_{rel_idx}"))
        obj = id_lookup.get(str(args[1]), normalize_entity_id(str(args[1]), prefix=DATASET, fallback=f"{doc_id}_arg2_{rel_idx}"))
        raw_pred = str(relation.get("type") or relation.get("relation_type") or relation.get("predicate") or "CID")
        relations.append(
            BioRelation(
                id=f"{doc_id}::rel-{rel_idx}",
                subj=subj,
                pred=map_bc5cdr_relation(raw_pred),
                obj=obj,
                metadata={"dataset": DATASET, "raw_relation_type": raw_pred, "source": "hf-parquet", "document_level": True},
            )
        )
    return BioDocument(id=doc_id, split=str(split_name), title=title, abstract=abstract, entities=entities, relations=relations, metadata={"source": "hf-parquet"})


def load_hf_parquet_documents() -> list[BioDocument]:
    try:
        from datasets import load_dataset  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency path
        raise RuntimeError("Install research dependencies with datasets to use --source hf-parquet") from exc

    payload = _read_json_url(HF_PARQUET_API_URL)
    data_files = parquet_payload_to_data_files(payload)
    try:
        dataset = load_dataset("parquet", data_files=data_files)
    except Exception as exc:  # pragma: no cover - network/schema dependent
        raise RuntimeError(
            "Could not load bigbio/bc5cdr converted Parquet files. "
            "If HuggingFace has no converted Parquet for this scripted dataset, use --source local with PubTator/BioC/JSONL raw files."
        ) from exc

    documents: list[BioDocument] = []
    for split_name, split_rows in dataset.items():  # pragma: no cover - optional live path
        canonical_split = "dev" if str(split_name) == "validation" else str(split_name)
        for row in split_rows:
            documents.append(bigbio_row_to_document(dict(row), canonical_split))
    return documents


def load_bigbio_documents() -> list[BioDocument]:
    """Legacy source name retained for compatibility.

    `datasets>=4` no longer supports loading dataset scripts with
    trust_remote_code. Route this source through HuggingFace converted Parquet
    instead and fail with an actionable message when converted Parquet is not
    available.
    """

    try:
        return load_hf_parquet_documents()
    except Exception as exc:
        raise RuntimeError(
            "The legacy --source bigbio path is no longer reliable with datasets>=4 because dataset scripts are not supported. "
            "Use --source hf-parquet, or use --source local after placing BC5CDR PubTator/BioC/JSONL files under --raw-dir. "
            "As a temporary legacy workaround only, a separate environment with datasets<4 may still load the old BigBio script."
        ) from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["local", "hf-parquet", "bigbio", "direct"], default="local")
    parser.add_argument("--raw-dir", default="data/biomedical/raw/bc5cdr")
    parser.add_argument("--download-dir", default="data/biomedical/raw/bc5cdr")
    parser.add_argument("--acquisition-manifest", default="data/biomedical/manifests/bc5cdr_acquisition_manifest.json")
    parser.add_argument("--out-dir", default="data/biomedical/processed")
    parser.add_argument("--manifest", default="data/biomedical/manifests/bc5cdr_manifest.json")
    parser.add_argument("--limit", type=int, default=None, help="Limit documents per split")
    args = parser.parse_args()

    try:
        if args.source == "local":
            documents = load_local_documents(args.raw_dir)
        elif args.source == "direct":
            direct_dir = download_direct_corpus(args.download_dir, args.acquisition_manifest)
            documents = load_local_documents(direct_dir)
        elif args.source == "hf-parquet":
            documents = load_hf_parquet_documents()
        else:
            documents = load_bigbio_documents()
    except (FileNotFoundError, RuntimeError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    outputs = write_graphtext_splits(args.out_dir, dataset=DATASET, documents=documents, limit=args.limit)
    split_counts = {split: sum(1 for doc in documents if doc.split.lower() in {split, split.replace("dev", "validation")}) for split in outputs}
    manifest = write_manifest(
        args.manifest,
        dataset=DATASET,
        source=args.source,
        status="converted",
        splits=split_counts,
        records=sum(split_counts.values()),
        source_url=DIRECT_SOURCE_URL if args.source == "direct" else SOURCE_URL,
        license_note=LICENSE_NOTE,
        notes=["BC5CDR conversion keeps document-level CID relations."],
        limitations=["BigBio field names can vary across dataset versions; local PubTator input is recommended for reproducibility."],
    )
    print(json.dumps({"outputs": outputs, "manifest": args.manifest, "records": manifest["records"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
