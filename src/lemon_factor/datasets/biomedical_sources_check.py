"""Report biomedical dataset acquisition status and recommended source paths."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from lemon_factor.datasets.biomedical_common import now_utc_iso

SOURCES: list[dict[str, Any]] = [
    {
        "dataset": "BC5CDR",
        "role": "chemical-disease relations",
        "direct_download": True,
        "local_required": False,
        "recommended_status": "primary",
        "direct_source": "https://github.com/openbiocorpora/biocreative-v-cdr",
        "command": "python -m lemon_factor.datasets.convert_bc5cdr --source direct --download-dir data/biomedical/raw/bc5cdr --out-dir data/biomedical/processed --manifest data/biomedical/manifests/bc5cdr_manifest.json --limit 200",
        "notes": "HF/BigBio scripted loader is unreliable with datasets>=4; direct raw mirror is preferred.",
    },
    {
        "dataset": "BioRED",
        "role": "document-level multi-type biomedical relations",
        "direct_download": True,
        "local_required": False,
        "recommended_status": "primary",
        "direct_source": "https://github.com/ncbi/BioRED",
        "command": "python -m lemon_factor.datasets.convert_biored --source direct --download-dir data/biomedical/raw/biored --out-dir data/biomedical/processed --manifest data/biomedical/manifests/biored_manifest.json --limit 200",
        "notes": "Official NCBI repository includes BIORED.zip with train/dev/test annotations.",
    },
    {
        "dataset": "DrugProt",
        "role": "chemical-gene/protein relations",
        "direct_download": True,
        "local_required": False,
        "recommended_status": "primary alternative to ChemProt",
        "direct_source": "https://zenodo.org/records/4955411",
        "command": "python -m lemon_factor.datasets.convert_drugprot --source direct --download-dir data/biomedical/raw/drugprot --out-dir data/biomedical/processed --manifest data/biomedical/manifests/drugprot_manifest.json --limit 200",
        "notes": "Zenodo record exposes abstracts/entities/relations TSV files for train/dev sets.",
    },
    {
        "dataset": "ChemProt",
        "role": "chemical-protein interactions",
        "direct_download": False,
        "local_required": True,
        "recommended_status": "optional/manual",
        "direct_source": "https://biocreative.bioinformatics.udel.edu/tasks/biocreative-vi/track-5/",
        "command": "python -m lemon_factor.datasets.convert_chemprot --raw-dir data/biomedical/raw/chemprot --out-dir data/biomedical/processed --manifest data/biomedical/manifests/chemprot_manifest.json --keep-relations CPR:3 CPR:4 CPR:5 CPR:6 CPR:9",
        "notes": "Use only if local ChemProt_Corpus.zip or extracted TSV files are available.",
    },
]


def write_markdown_table(rows: list[dict[str, Any]], path: str | Path) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "| Dataset | Role | Direct download | Local required | Recommended status |",
        "|---|---|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {dataset} | {role} | {direct} | {local} | {status} |".format(
                dataset=row["dataset"],
                role=row["role"],
                direct="yes" if row["direct_download"] else "no",
                local="yes" if row["local_required"] else "no",
                status=row["recommended_status"],
            )
        )
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="data/biomedical/reports/biomedical_sources_check.json")
    parser.add_argument("--table", default="paper/tables/table_biomedical_sources_check.md")
    args = parser.parse_args()

    payload = {"generated_at": now_utc_iso(), "sources": SOURCES}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown_table(SOURCES, args.table)
    print(json.dumps({"out": args.out, "table": args.table, "sources": len(SOURCES)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
