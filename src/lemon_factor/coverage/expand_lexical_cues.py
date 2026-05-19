"""Expand WebNLG lexical cues for predicates observed as coverage misses."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lemon_factor.coverage.missing_analysis import MissingPredicateReport
from lemon_factor.coverage.text_evidence import normalize_text
from lemon_factor.factors.candidates import candidate_factors_from_predicate

TEMPLATE_CUES: dict[str, list[str]] = {
    "author": ["author", "written by", "wrote", "writer"],
    "battle": ["battle", "fought in", "served in"],
    "capital": ["capital", "capital of"],
    "city": ["city", "in", "located in"],
    "country": ["country", "in", "located in"],
    "creator": ["creator", "created by", "made by"],
    "date": ["date", "on", "in"],
    "death": ["died", "died in", "death", "death place"],
    "developer": ["developed by", "developer"],
    "elevation": ["elevation", "above sea level"],
    "genre": ["genre", "type", "style"],
    "ground": ["ground", "home ground", "stadium"],
    "headquarter": ["headquartered", "headquarters", "based in"],
    "leader": ["leader", "mayor", "president", "governor", "led by"],
    "length": ["length", "long", "feet", "metres", "meters"],
    "language": ["language", "written in", "spoken", "in"],
    "location": ["located in", "location", "based in", "in"],
    "manufacturer": ["manufactured by", "manufacturer", "made by", "built by"],
    "mayor": ["mayor", "led by"],
    "member": ["member", "members", "member of"],
    "operator": ["operated by", "operator", "run by"],
    "owner": ["owned by", "owner"],
    "part": ["part of", "belongs to", "included in"],
    "population": ["population", "people", "inhabitants"],
    "product": ["product", "produces", "made"],
    "region": ["region", "area", "located in"],
    "runway": ["runway", "runway length", "runway name"],
    "team": ["team", "club", "plays for"],
    "title": ["title", "office", "position"],
}


def load_cues(path: str | Path | None) -> dict[str, list[str]]:
    if path is None or not Path(path).exists():
        return {}
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return {str(key): [str(item) for item in value] for key, value in raw.items()}


def _dedupe(cues: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for cue in cues:
        norm = normalize_text(cue)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        out.append(cue)
    return out


def cues_from_predicate(predicate: str) -> list[str]:
    tokens = candidate_factors_from_predicate(predicate)
    cues: list[str] = [predicate, " ".join(tokens)]
    for token in tokens:
        cues.append(token)
        cues.extend(TEMPLATE_CUES.get(token.lower(), []))
    if "birth" in tokens and "place" in tokens:
        cues.extend(["born in", "birthplace", "place of birth"])
    if "birth" in tokens and ("date" in tokens or "year" in tokens):
        cues.extend(["born on", "born in", "date of birth"])
    if "death" in tokens and "place" in tokens:
        cues.extend(["died in", "place of death"])
    if "is" in tokens and "part" in tokens:
        cues.extend(["is part of", "part of"])
    if "associated" in tokens and "artist" in tokens:
        cues.extend(["associated with", "played with", "member of"])
    return _dedupe(cues)


def expand_lexical_cues(
    base_cues: dict[str, list[str]],
    missing_report: MissingPredicateReport,
    *,
    max_predicates: int | None = None,
) -> dict[str, list[str]]:
    expanded = {key: list(value) for key, value in base_cues.items()}
    items = list(missing_report.predicates.values())
    if max_predicates is not None:
        items = items[:max_predicates]
    for item in items:
        current = expanded.get(item.predicate, [])
        expanded[item.predicate] = _dedupe(current + cues_from_predicate(item.predicate))
    return dict(sorted(expanded.items()))


def write_cues(cues: dict[str, list[str]], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cues, ensure_ascii=False, indent=2), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--missing", required=True, help="Missing-predicate JSON report")
    parser.add_argument("--base-cues", default=None, help="Existing lexical cues JSON")
    parser.add_argument("--out", required=True, help="Expanded lexical cues JSON")
    parser.add_argument("--max-predicates", type=int, default=None)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    missing = MissingPredicateReport.from_json_file(args.missing)
    cues = expand_lexical_cues(load_cues(args.base_cues), missing, max_predicates=args.max_predicates)
    write_cues(cues, args.out)
    print(json.dumps({"out": args.out, "cue_predicates": len(cues)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
