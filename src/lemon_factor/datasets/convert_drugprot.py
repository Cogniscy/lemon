"""Convert DrugProt chemical--gene/protein relation data to GraphText JSONL.

Supported inputs:
- local DrugProt TSV folders/files with abstracts, entities, and relations;
- --source direct downloads DrugProt files from Zenodo record 4955411.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

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
from lemon_factor.datasets.biomedical_download import (
    DownloadError,
    download_zenodo_record_files,
    extract_zip,
    write_acquisition_manifest,
)

DATASET = "drugprot"
ZENODO_RECORD_ID = "4955411"
SOURCE_URL = f"https://zenodo.org/records/{ZENODO_RECORD_ID}"
LICENSE_NOTE = "DrugProt is distributed through Zenodo/BioCreative VII; verify current license and redistribution terms."

RELATION_MAP = {
    "ACTIVATOR": "chemical_activates_gene_or_protein",
    "INHIBITOR": "chemical_inhibits_gene_or_protein",
    "INDIRECT-UPREGULATOR": "chemical_indirectly_upregulates_gene_or_protein",
    "INDIRECT_UPREGULATOR": "chemical_indirectly_upregulates_gene_or_protein",
    "INDIRECT-DOWNREGULATOR": "chemical_indirectly_downregulates_gene_or_protein",
    "INDIRECT_DOWNREGULATOR": "chemical_indirectly_downregulates_gene_or_protein",
    "SUBSTRATE": "chemical_substrate_of_gene_or_protein",
    "PRODUCT-OF": "chemical_product_of_gene_or_protein",
    "PRODUCT_OF": "chemical_product_of_gene_or_protein",
    "SUBSTRATE_PRODUCT-OF": "chemical_substrate_product_of_gene_or_protein",
    "SUBSTRATE_PRODUCT_OF": "chemical_substrate_product_of_gene_or_protein",
    "PART-OF": "part_of_relation",
    "PART_OF": "part_of_relation",
    "AGONIST": "chemical_agonist_of_gene_or_protein",
    "AGONIST-ACTIVATOR": "chemical_agonist_activator_of_gene_or_protein",
    "AGONIST_ACTIVATOR": "chemical_agonist_activator_of_gene_or_protein",
    "AGONIST-INHIBITOR": "chemical_agonist_inhibitor_of_gene_or_protein",
    "AGONIST_INHIBITOR": "chemical_agonist_inhibitor_of_gene_or_protein",
    "ANTAGONIST": "chemical_antagonist_of_gene_or_protein",
    "DIRECT-REGULATOR": "chemical_directly_regulates_gene_or_protein",
    "DIRECT_REGULATOR": "chemical_directly_regulates_gene_or_protein",
}


def map_drugprot_relation(raw: str) -> str:
    value = raw.strip().upper().replace(" ", "_")
    return RELATION_MAP.get(value, value.lower().replace("-", "_").replace(":", "_"))


def map_drugprot_entity_type(raw: str) -> str:
    value = raw.strip().lower()
    if value in {"chemical", "chem", "chemical_entity", "compound"}:
        return "Chemical"
    if value in {"gene", "protein", "gene-y", "gene-n", "gene/protein", "gene_protein"}:
        return "GeneOrProtein"
    return raw.strip() or "Entity"


def _extract_arg(value: str) -> str:
    value = value.strip()
    if ":" in value:
        return value.split(":")[-1]
    return value


def _is_abstract_file(path: Path) -> bool:
    """Return True for DrugProt abstract TSV names.

    The official DrugProt Gold Standard archive uses the misspelled file name
    ``drugprot_training_abstracs.tsv``.  Accept both spellings so the parser
    keeps title and abstract text instead of producing graph examples with empty
    ``text`` fields.
    """

    name = path.name.lower()
    return "abstract" in name or "abstrac" in name


def _has_extracted_drugprot_files(path: str | Path) -> bool:
    base = Path(path)
    if not base.exists():
        return False
    return bool(choose_local_files(base, ["*.tsv"]))


def _extract_existing_archives(path: str | Path) -> None:
    base = Path(path)
    for archive in sorted(base.glob("*.zip")):
        target = base / archive.stem
        if target.exists() and any(target.iterdir()):
            continue
        extract_zip(archive, target)


def parse_drugprot_tsv(raw_dir: str | Path) -> list[BioDocument]:
    files = choose_local_files(raw_dir, ["*.tsv", "*.txt"])
    abstracts: dict[str, dict[str, str]] = defaultdict(lambda: {"title": "", "abstract": "", "split": "pilot"})
    entities: dict[str, list[BioEntity]] = defaultdict(list)
    relations: dict[str, list[BioRelation]] = defaultdict(list)

    for path in files:
        split = infer_split_from_name(path)
        lower = path.name.lower()
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.lower().startswith("pmid"):
                continue
            parts = line.rstrip("\n").split("\t")
            if _is_abstract_file(path) and len(parts) >= 3:
                pmid, title, abstract = parts[0], parts[1], parts[2]
                abstracts[pmid] = {"title": title, "abstract": abstract, "split": split}
            elif "entit" in lower and len(parts) >= 6:
                pmid, ent_id, ent_type, start, end, mention = parts[:6]
                node_id = normalize_entity_id(ent_id, prefix=DATASET, fallback=f"{pmid}_{mention}")
                entities[pmid].append(
                    BioEntity(
                        id=node_id,
                        label=mention,
                        type=map_drugprot_entity_type(ent_type),
                        external_id=ent_id,
                        metadata={"source_entity_id": ent_id, "start": start, "end": end, "source_file": str(path)},
                    )
                )
                abstracts[pmid]["split"] = split
            elif "relation" in lower and len(parts) >= 4:
                pmid = parts[0]
                rel_type = parts[1]
                arg1 = _extract_arg(parts[2])
                arg2 = _extract_arg(parts[3])
                relations[pmid].append(
                    BioRelation(
                        id=f"{pmid}::{rel_type}::{len(relations[pmid])}",
                        subj=normalize_entity_id(arg1, prefix=DATASET, fallback=f"{pmid}_arg1"),
                        pred=map_drugprot_relation(rel_type),
                        obj=normalize_entity_id(arg2, prefix=DATASET, fallback=f"{pmid}_arg2"),
                        metadata={"dataset": DATASET, "raw_relation_type": rel_type, "source_file": str(path), "document_level": False},
                    )
                )
                abstracts[pmid]["split"] = split

    documents: list[BioDocument] = []
    for pmid in sorted(set(abstracts) | set(entities) | set(relations)):
        documents.append(
            BioDocument(
                id=pmid,
                split=abstracts[pmid]["split"],
                title=abstracts[pmid].get("title", ""),
                abstract=abstracts[pmid].get("abstract", ""),
                entities=entities[pmid],
                relations=relations[pmid],
                metadata={"source_format": "drugprot_tsv", "document_level": False},
            )
        )
    return documents


def load_local_documents(raw_dir: str | Path) -> list[BioDocument]:
    base = Path(raw_dir)
    if not base.exists():
        raise FileNotFoundError(
            missing_raw_dir_message(
                raw_dir,
                dataset="DrugProt",
                source_hint="place DrugProt abstracts/entities/relations TSV files there, or run with --source direct to download from Zenodo.",
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
                relation_mapper=map_drugprot_relation,
                entity_type_mapper=map_drugprot_entity_type,
            )
        )
    documents.extend(parse_drugprot_tsv(base))
    if not documents:
        raise FileNotFoundError(
            no_raw_files_message(
                base,
                dataset="DrugProt",
                expected="*.json, *.jsonl, *.tsv, or *.txt",
                source_hint="Use --source direct or place DrugProt train/dev TSV files from Zenodo here.",
            )
        )
    return documents


def download_direct_corpus(download_dir: str | Path, acquisition_manifest: str | Path | None = None) -> Path:
    out_dir = Path(download_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not _has_extracted_drugprot_files(out_dir):
        _extract_existing_archives(out_dir)
    if _has_extracted_drugprot_files(out_dir):
        if acquisition_manifest:
            write_acquisition_manifest(
                acquisition_manifest,
                dataset=DATASET,
                source_type="local_zenodo_archive",
                source_url=SOURCE_URL,
                raw_dir=out_dir,
                status="reused_existing_raw_files",
                license_note=LICENSE_NOTE,
                notes=["Reused existing DrugProt TSV files or an already downloaded Zenodo archive."],
            )
        return out_dir

    try:
        files = download_zenodo_record_files(ZENODO_RECORD_ID, out_dir)
        for path in files:
            if path.suffix.lower() == ".zip":
                extract_zip(path, out_dir / path.stem)
    except DownloadError as exc:  # pragma: no cover - network dependent
        raise RuntimeError(
            "Could not download DrugProt from Zenodo. Manual fallback: download the DrugProt corpus from "
            f"{SOURCE_URL} and place abstracts/entities/relations TSV files under {out_dir}."
        ) from exc
    if acquisition_manifest:
        write_acquisition_manifest(
            acquisition_manifest,
            dataset=DATASET,
            source_type="zenodo_record",
            source_url=SOURCE_URL,
            raw_dir=out_dir,
            status="downloaded",
            license_note=LICENSE_NOTE,
            notes=["Downloaded DrugProt files from Zenodo record 4955411."],
        )
    return out_dir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["local", "direct"], default="local")
    parser.add_argument("--raw-dir", default="data/biomedical/raw/drugprot")
    parser.add_argument("--download-dir", default="data/biomedical/raw/drugprot")
    parser.add_argument("--acquisition-manifest", default="data/biomedical/manifests/drugprot_acquisition_manifest.json")
    parser.add_argument("--out-dir", default="data/biomedical/processed")
    parser.add_argument("--manifest", default="data/biomedical/manifests/drugprot_manifest.json")
    parser.add_argument("--limit", type=int, default=None, help="Limit documents per split")
    args = parser.parse_args()

    try:
        if args.source == "direct":
            raw_dir = download_direct_corpus(args.download_dir, args.acquisition_manifest)
            documents = load_local_documents(raw_dir)
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
        notes=["DrugProt conversion maps chemical-gene/protein relations into biomedical predicates."],
        limitations=["DrugProt relation direction is preserved from the raw relation arguments."],
    )
    print(json.dumps({"outputs": outputs, "manifest": args.manifest, "records": manifest["records"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
