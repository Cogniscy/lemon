"""Convert ChemProt chemical--protein interaction data to GraphText JSONL.

Supported local inputs:
- simple JSON/JSONL fixtures with entities and relations;
- ChemProt-like TSV files containing abstracts, entities, and relations.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

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

DATASET = "chemprot"
SOURCE_URL = "https://biocreative.bioinformatics.udel.edu/tasks/biocreative-vi/track-5/"
LICENSE_NOTE = "ChemProt was released for BioCreative VI; verify current access terms before redistribution."

CPR_TO_PREDICATE = {
    "CPR:3": "chemical_upregulates_protein",
    "CPR:4": "chemical_downregulates_protein",
    "CPR:5": "chemical_agonist_of_protein",
    "CPR:6": "chemical_antagonist_of_protein",
    "CPR:9": "chemical_substrate_or_product_of_protein",
}


def map_chemprot_relation(raw: str) -> str:
    value = raw.strip().upper().replace("CPR_", "CPR:")
    return CPR_TO_PREDICATE.get(value, value.lower().replace(":", "_").replace("-", "_"))


def map_chemprot_entity_type(raw: str) -> str:
    value = raw.strip().lower()
    if value in {"chemical", "chemical_entity", "compound"}:
        return "Chemical"
    if value in {"protein", "gene", "gene-y", "gene/protein"}:
        return "Protein"
    return raw.strip() or "Entity"


def _extract_arg(value: str) -> str:
    # Handles Arg1:T1, T1, CHEMICAL:T1, etc.
    value = value.strip()
    if ":" in value:
        return value.split(":")[-1]
    return value


def parse_chemprot_tsv(raw_dir: str | Path, keep_relations: set[str] | None = None) -> list[BioDocument]:
    files = choose_local_files(raw_dir, ["*.tsv", "*.txt"])
    if not files:
        return []
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
            if "abstract" in lower and len(parts) >= 3:
                pmid, title, abstract = parts[0], parts[1], parts[2]
                abstracts[pmid] = {"title": title, "abstract": abstract, "split": split}
            elif "entit" in lower and len(parts) >= 6:
                pmid, ent_id, ent_type, start, end, mention = parts[:6]
                node_id = normalize_entity_id(ent_id, prefix=DATASET, fallback=f"{pmid}_{mention}")
                entities[pmid].append(
                    BioEntity(
                        id=node_id,
                        label=mention,
                        type=map_chemprot_entity_type(ent_type),
                        external_id=ent_id,
                        metadata={"source_entity_id": ent_id, "start": start, "end": end, "source_file": str(path)},
                    )
                )
                abstracts[pmid]["split"] = split
            elif "relation" in lower and len(parts) >= 4:
                pmid = parts[0]
                rel_type = next((p for p in parts if re.match(r"CPR[:_]\d+", p, flags=re.I)), parts[1])
                rel_type = rel_type.upper().replace("CPR_", "CPR:")
                if keep_relations and rel_type not in keep_relations:
                    continue
                arg_like = [p for p in parts[1:] if ":" in p and not p.upper().startswith("CPR:")]
                if len(arg_like) >= 2:
                    arg1, arg2 = _extract_arg(arg_like[0]), _extract_arg(arg_like[1])
                else:
                    arg1, arg2 = _extract_arg(parts[-2]), _extract_arg(parts[-1])
                relations[pmid].append(
                    BioRelation(
                        id=f"{pmid}::{rel_type}::{len(relations[pmid])}",
                        subj=normalize_entity_id(arg1, prefix=DATASET, fallback=f"{pmid}_arg1"),
                        pred=map_chemprot_relation(rel_type),
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
                metadata={"source_format": "chemprot_tsv"},
            )
        )
    return documents


def load_local_documents(raw_dir: str | Path, keep_relations: set[str] | None = None) -> list[BioDocument]:
    base = Path(raw_dir)
    if not base.exists():
        raise FileNotFoundError(
            missing_raw_dir_message(
                raw_dir,
                dataset="ChemProt",
                source_hint="place ChemProt abstracts/entities/relations TSV files or JSON/JSONL fixtures there.",
            )
        )
    documents: list[BioDocument] = []
    json_files = choose_local_files(base, ["*.json", "*.jsonl"])
    for path in json_files:
        json_docs = json_records_to_documents(
            read_json_records(path),
            dataset=DATASET,
            default_split=infer_split_from_name(path),
            relation_mapper=map_chemprot_relation,
            entity_type_mapper=map_chemprot_entity_type,
        )
        for doc in json_docs:
            doc.metadata.setdefault("document_level", False)
            for relation in doc.relations:
                relation.metadata["document_level"] = False
        documents.extend(json_docs)
    documents.extend(parse_chemprot_tsv(base, keep_relations=keep_relations))
    if not documents:
        raise FileNotFoundError(
            no_raw_files_message(
                base,
                dataset="ChemProt",
                expected="*.json, *.jsonl, *.tsv, or *.txt",
                source_hint="Place ChemProt abstracts/entities/relations TSV files there; access may require manual BioCreative download.",
            )
        )
    return documents


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", default="data/biomedical/raw/chemprot")
    parser.add_argument("--out-dir", default="data/biomedical/processed")
    parser.add_argument("--manifest", default="data/biomedical/manifests/chemprot_manifest.json")
    parser.add_argument("--keep-relations", nargs="*", default=["CPR:3", "CPR:4", "CPR:5", "CPR:6", "CPR:9"])
    parser.add_argument("--limit", type=int, default=None, help="Limit documents per split")
    args = parser.parse_args()

    keep = {item.upper().replace("CPR_", "CPR:") for item in args.keep_relations} if args.keep_relations else None
    try:
        documents = load_local_documents(args.raw_dir, keep_relations=keep)
    except FileNotFoundError as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    outputs = write_graphtext_splits(args.out_dir, dataset=DATASET, documents=documents, limit=args.limit)
    split_counts = {split: sum(1 for doc in documents if doc.split.lower() == split) for split in outputs}
    manifest = write_manifest(
        args.manifest,
        dataset=DATASET,
        source="local",
        status="converted",
        splits=split_counts,
        records=sum(split_counts.values()),
        source_url=SOURCE_URL,
        license_note=LICENSE_NOTE,
        notes=["ChemProt conversion keeps evaluation CPR classes by default: CPR:3, CPR:4, CPR:5, CPR:6, CPR:9."],
        limitations=["Raw ChemProt access may require manual download from BioCreative resources."],
    )
    print(json.dumps({"outputs": outputs, "manifest": args.manifest, "records": manifest["records"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
