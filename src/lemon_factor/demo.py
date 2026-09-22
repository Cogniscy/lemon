"""Small packaged examples using the real lexical scorer."""
from __future__ import annotations

import hashlib
import json
from importlib.metadata import PackageNotFoundError, version
from importlib.resources import files
from pathlib import Path

from lemon_factor.coverage.factor_coverage import score_predicate_decomposition
from lemon_factor.factors.decomposition import PredicateDecomposition
from lemon_factor.schema.graphtext import Edge


def resource_bytes() -> bytes:
    return files("lemon_factor").joinpath("demo_data/cases.json").read_bytes()


def build_demo() -> dict:
    data = json.loads(resource_bytes())
    edge = Edge.model_validate(data["source_edge"])
    decomposition = PredicateDecomposition.model_validate(data["decomposition"])
    try:
        package_version = version("lemon-factor")
    except PackageNotFoundError:
        package_version = "uninstalled"
    cases = []
    for case in data["cases"]:
        result = score_predicate_decomposition(
            decomposition, case["text"], edge, data["node_labels"], data["lexical_cues"]
        )
        cases.append({
            **case, "source_edge": edge.model_dump(), "node_labels": data["node_labels"],
            "score": result.score,
            "components": [component.model_dump() for component in result.components],
        })
    return {
        "schema_version": "1", "method": "lexical_factor_coverage",
        "package_version": package_version, "cases": cases,
    }


def render_demo(report: dict) -> str:
    lines = ["LEMON lexical factor coverage", "Scores measure lexical evidence, not entailment.", ""]
    for case in report["cases"]:
        labels = case["node_labels"]
        edge = case["source_edge"]
        lines.extend([
            f"[{case['id']}] {labels[edge['subj']]} --{edge['pred']}--> {labels[edge['obj']]}",
            case["text"], f"Score: {case['score']:.4f}",
            "Factor | Role | Weight | Score | Evidence",
        ])
        for component in case["components"]:
            lines.append(
                f"{component['factor']} | {component['role']} | {component['weight']:.2f} | "
                f"{component['score']:.2f} | {component['evidence_type']}"
            )
        if case["known_limitation"]:
            lines.append("Known limitation: " + case["known_limitation"])
        lines.append("")
    return "\n".join(lines)


def reproduce_demo(out: Path, *, overwrite: bool = False) -> dict:
    report = build_demo()
    data = json.loads(resource_bytes())
    manifest = {
        "schema_version": "1", "method": report["method"],
        "package_version": report["package_version"],
        "input_sha256": {"demo_data/cases.json": hashlib.sha256(resource_bytes()).hexdigest()},
        "configuration": {
            "decomposition": data["decomposition"], "lexical_cues": data["lexical_cues"],
        },
        "scope": "Illustrative synthetic cases; not a reproduction of the paper experiments.",
    }
    summary = [
        "# Lexical coverage demo", "", manifest["scope"], "",
        "| Case | Score | Known limitation |", "|---|---:|---|",
    ]
    for case in report["cases"]:
        summary.append(f"| {case['id']} | {case['score']:.4f} | {case['known_limitation'] or ''} |")
    payloads = {
        "scores.json": json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        "summary.md": "\n".join(summary) + "\n",
        "manifest.json": json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    }
    # Check every destination before writing any output.
    for name in payloads:
        destination = out / name
        if destination.is_symlink() or (destination.exists() and not destination.is_file()):
            raise ValueError(f"Output is not a regular file: {destination}")
        if destination.exists() and not overwrite:
            raise FileExistsError(f"{destination} exists; use --overwrite to replace demo outputs.")
    out.mkdir(parents=True, exist_ok=True)
    for name, content in payloads.items():
        with (out / name).open("w" if overwrite else "x", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
    return manifest
