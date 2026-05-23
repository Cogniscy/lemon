"""Convert BioRED document-level biomedical relation data to GraphText JSONL.

Supported local inputs:
- simple JSON/JSONL fixtures with entities and relations;
- PubTator-like BioRED files with document titles/abstracts, entity rows, and relation rows.
"""

from __future__ import annotations

import argparse
import json
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

DATASET = "biored"
SOURCE_URL = "https://github.com/ncbi/BioRED"
LICENSE_NOTE = "BioRED is distributed by NCBI; verify current access and redistribution terms."

RELATION_MAP = {
    "ASSOCIATION": "biomedical_association",
    "POSITIVE_CORRELATION": "positive_correlation",
    "NEGATIVE_CORRELATION": "negative_correlation",
    "DRUG_INTERACTION": "drug_interaction",
    "BINDING": "biomolecular_binding",
    "COTREATMENT": "cotreatment",
    "CONVERSION": "biochemical_conversion",
    "COMPARISON": "biomedical_comparison",
}

ENTITY_TYPE_MAP = {
    "GENE": "GeneOrProtein",
    "GENE/PROTEIN": "GeneOrProtein",
    "DISEASE": "Disease",
    "CHEMICAL": "Chemical",
    "VARIANT": "Variant",
    "SPECIES": "Species",
    "CELL_LINE": "CellLine",
    "CELL LINE": "CellLine",
}


def map_biored_relation(raw: str) -> str:
    value = raw.strip().upper().replace(" ", "_").replace("-", "_")
    return RELATION_MAP.get(value, value.lower())


def map_biored_entity_type(raw: str) -> str:
    value = raw.strip().upper().replace("-", "_")
    return ENTITY_TYPE_MAP.get(value, raw.strip() or "Entity")


def parse_biored_pubtator_files(paths: list[Path]) -> list[BioDocument]:
    documents: list[BioDocument] = []
    for path in paths:
        split = infer_split_from_name(path)
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

        for line in path.read_text(encoding="utf-8").splitlines() + [""]:
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
            if current is None:
                continue
            parts = stripped.split("\t")
            if len(parts) >= 6 and parts[1].isdigit():
                pmid, start, end, mention, ent_type, external_id = parts[:6]
                entity_id = normalize_entity_id(external_id or mention, prefix=DATASET, fallback=f"{pmid}_{start}_{end}_{mention}")
                entities.append(
                    BioEntity(
                        id=entity_id,
                        label=mention,
                        type=map_biored_entity_type(ent_type),
                        external_id=external_id,
                        metadata={"start": int(start), "end": int(end), "source_file": str(path)},
                    )
                )
            elif len(parts) >= 4:
                pmid, relation_type, arg1, arg2 = parts[:4]
                novelty = parts[4] if len(parts) > 4 else None
                relations.append(
                    BioRelation(
                        id=f"{pmid}::{relation_type}::{len(relations)}",
                        subj=normalize_entity_id(arg1, prefix=DATASET, fallback=f"{pmid}_arg1"),
                        pred=map_biored_relation(relation_type),
                        obj=normalize_entity_id(arg2, prefix=DATASET, fallback=f"{pmid}_arg2"),
                        metadata={
                            "dataset": DATASET,
                            "raw_relation_type": relation_type,
                            "novelty": novelty,
                            "source_file": str(path),
                            "document_level": True,
                        },
                    )
                )
    return documents


def load_local_documents(raw_dir: str | Path) -> list[BioDocument]:
    base = Path(raw_dir)
    if not base.exists():
        raise FileNotFoundError(
            missing_raw_dir_message(
                raw_dir,
                dataset="BioRED",
                source_hint="place BioRED PubTator/JSON/JSONL files there after downloading the corpus.",
            )
        )
    documents: list[BioDocument] = []
    json_files = choose_local_files(base, ["*.json", "*.jsonl"])
    for path in json_files:
        documents.extend(
            json_records_to_documents(
                read_json_records(path),
                dataset=DATASET,
                default_split=infer_split_from_name(path),
                relation_mapper=map_biored_relation,
                entity_type_mapper=map_biored_entity_type,
            )
        )
    pubtator_files = [p for p in choose_local_files(base, ["*.PubTator*", "*.pubtator*", "*.txt"]) if p not in json_files]
    if pubtator_files:
        documents.extend(parse_biored_pubtator_files(pubtator_files))
    if not documents:
        raise FileNotFoundError(
            no_raw_files_message(
                base,
                dataset="BioRED",
                expected="*.json, *.jsonl, *.PubTator*, *.pubtator*, or *.txt",
                source_hint="Place BioRED PubTator/JSON/JSONL files there after downloading the corpus.",
            )
        )
    return documents


def download_direct_corpus(download_dir: str | Path, acquisition_manifest: str | Path | None = None) -> Path:
    """Download the official NCBI BioRED repository archive and extract nested corpus zip files."""

    out_dir = Path(download_dir)
    try:
        download_github_repo_zip("ncbi", "BioRED", out_dir, branch="master")
        extract_nested_zips(out_dir)
    except DownloadError as exc:  # pragma: no cover - network dependent
        raise RuntimeError(
            "Could not download BioRED directly. Manual fallback: download BIORED.zip from "
            f"{SOURCE_URL} and place PubTator/JSON files under {out_dir}."
        ) from exc
    if acquisition_manifest:
        write_acquisition_manifest(
            acquisition_manifest,
            dataset=DATASET,
            source_type="github_repo_zip",
            source_url=SOURCE_URL,
            raw_dir=out_dir,
            status="downloaded",
            license_note=LICENSE_NOTE,
            notes=["Downloaded the official NCBI BioRED repository archive and extracted nested zips."],
            limitations=["BioRED relations can be document-level and cross-sentence."],
        )
    return out_dir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["local", "direct"], default="local")
    parser.add_argument("--raw-dir", default="data/biomedical/raw/biored")
    parser.add_argument("--download-dir", default="data/biomedical/raw/biored")
    parser.add_argument("--acquisition-manifest", default="data/biomedical/manifests/biored_acquisition_manifest.json")
    parser.add_argument("--out-dir", default="data/biomedical/processed")
    parser.add_argument("--manifest", default="data/biomedical/manifests/biored_manifest.json")
    parser.add_argument("--limit", type=int, default=None, help="Limit documents per split")
    args = parser.parse_args()

    try:
        if args.source == "direct":
            direct_dir = download_direct_corpus(args.download_dir, args.acquisition_manifest)
            documents = load_local_documents(direct_dir)
        else:
            documents = load_local_documents(args.raw_dir)
    except (FileNotFoundError, RuntimeError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    outputs = write_graphtext_splits(args.out_dir, dataset=DATASET, documents=documents, limit=args.limit)
    split_counts = {split: sum(1 for doc in documents if doc.split.lower() == split) for split in outputs}
    manifest = write_manifest(
        args.manifest,
        dataset=DATASET,
        source=args.source,
        status="converted",
        splits=split_counts,
        records=sum(split_counts.values()),
        source_url=SOURCE_URL,
        license_note=LICENSE_NOTE,
        notes=["BioRED conversion keeps document-level multi-type relation annotations."],
        limitations=["BioRED relation evidence can be cross-sentence; conversion uses whole title+abstract text."],
    )
    print(json.dumps({"outputs": outputs, "manifest": args.manifest, "records": manifest["records"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
