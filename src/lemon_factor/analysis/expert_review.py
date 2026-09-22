"""Reproduce the pilot expert trace review using a declared six-category scale."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

LABELS = ("contradicted", "lost", "mostly_lost", "partial", "mostly_preserved", "preserved")
RUSSIAN_LABELS = (
    "противоречит", "потерян", "скорее потерян",
    "частично", "скорее сохранён", "сохранён",
)
ALIASES = dict(zip(RUSSIAN_LABELS, LABELS))
FIELDS = ("reviewer_id", "example_id", "row_id", "domain", "error_type",
          "triple", "text", "factor", "role", "weight", "lemon_trace", "expert_trace")
SHARED = FIELDS[1:-1]


def repair_separators(text: str) -> str:
    """Repair literal backslash-n record separators only outside quoted fields."""
    out = []
    quoted = False
    i = 0
    while i < len(text):
        if text[i] == '"':
            if quoted and text[i:i+2] == '""':
                out.append('""')
                i += 2
                continue
            quoted = not quoted
        if not quoted and text[i:i+2] == "\\n":
            out.append("\n")
            i += 2
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def label(value: str) -> str:
    value = value.strip().lower().replace("ё", "е")
    aliases = {k.replace("ё", "е"): v for k, v in ALIASES.items()}
    value = aliases.get(value, value)
    if value not in LABELS:
        raise ValueError(f"Unknown trace label: {value!r}")
    return value


def import_exports(paths: list[Path]) -> tuple[list[dict], dict]:
    ratings = []
    manifests = []
    seen_hashes = set()
    source_reviewers = set()
    for path in sorted(paths):
        raw = path.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        if sha in seen_hashes:
            raise ValueError("Duplicate source file")
        seen_hashes.add(sha)
        text = raw.decode("utf-8-sig")
        repaired = repair_separators(text)
        rows = list(csv.DictReader(io.StringIO(repaired)))
        if not rows or not set(FIELDS).issubset(rows[0]):
            raise ValueError(f"Missing review columns in {path.name}")
        completed = [r for r in rows if r["expert_trace"].strip()]
        info = {"sha256": sha, "rows": len(rows), "escaped_record_separators": repaired != text}
        if not completed:
            manifests.append({**info, "status": "excluded_empty_template"})
            continue
        if len(completed) != len(rows):
            raise ValueError(f"Partially completed review in {path.name}; explicit missing-data handling required")
        identities = {r["reviewer_id"] for r in rows}
        if len(identities) != 1 or not next(iter(identities)).strip():
            raise ValueError("Expected one nonempty reviewer ID per export")
        source_id = next(iter(identities))
        if source_id in source_reviewers:
            raise ValueError("Duplicate reviewer ID across exports")
        source_reviewers.add(source_id)
        reviewer = f"R{len(source_reviewers)}"
        for row in rows:
            item = {k: row[k] for k in FIELDS}
            item["reviewer_id"] = reviewer
            item["lemon_trace"] = label(item["lemon_trace"])
            item["expert_trace"] = label(item["expert_trace"])
            weight = float(item["weight"])
            if not math.isfinite(weight) or weight <= 0:
                raise ValueError("Weights must be finite and positive")
            item["weight"] = weight
            ratings.append(item)
        manifests.append({**info, "status": "included", "reviewer_id": reviewer})
    if not ratings:
        raise ValueError("No completed reviews")
    summarize(ratings)  # Validate alignment before any output is written.
    return ratings, {
        "schema_version": "expert-import-v1", "sources": manifests,
        "anonymization": "Reviewer IDs replaced; source IDs, filenames, comments, confidence and severity omitted.",
        "normalization": "UTF-8 BOM accepted; literal record separators repaired outside quotes only; Russian labels mapped explicitly.",
    }


def wilson(successes: int, total: int) -> list[float]:
    z = 1.959963984540054
    p = successes / total
    denom = 1 + z*z/total
    center = (p + z*z/(2*total)) / denom
    half = z * math.sqrt(p*(1-p)/total + z*z/(4*total*total)) / denom
    return [center-half, center+half]


def summarize(ratings: list[dict]) -> dict:
    units = defaultdict(dict)
    shared = {}
    for row in ratings:
        rid, reviewer = row["row_id"], row["reviewer_id"]
        if reviewer in units[rid]:
            raise ValueError(f"Duplicate reviewer/row pair: {reviewer}/{rid}")
        weight = float(row["weight"])
        if not math.isfinite(weight) or weight <= 0:
            raise ValueError("Weights must be finite and positive")
        signature = tuple(weight if k == "weight" else row[k] for k in SHARED)
        if rid in shared and shared[rid] != signature:
            raise ValueError(f"Inconsistent source metadata: {rid}")
        shared[rid] = signature
        if row["lemon_trace"] not in LABELS or row["expert_trace"] not in LABELS:
            raise ValueError("Normalized ratings contain unknown labels")
        units[rid][reviewer] = row
    if not units:
        raise ValueError("No ratings")
    reviewers = set(next(iter(units.values())))
    if len(reviewers) < 2 or any(set(unit) != reviewers for unit in units.values()):
        raise ValueError("Require the same two or more reviewers on every row")
    n = len(ratings)
    m = len(reviewers)
    exact = sum(r["lemon_trace"] == r["expert_trace"] for r in ratings)
    lemon_counts = Counter(r["lemon_trace"] for r in ratings)
    expert_counts = Counter(r["expert_trace"] for r in ratings)
    chance = sum(lemon_counts[k]*expert_counts[k] for k in LABELS) / n**2
    pooled_kappa = (exact/n-chance)/(1-chance) if chance < 1 else None
    counts = [Counter(r["expert_trace"] for r in unit.values()) for unit in units.values()]
    observed = sum(sum(v*(v-1) for v in c.values()) / (m*(m-1)) for c in counts)/len(counts)
    chance_inter = sum((v/n)**2 for v in expert_counts.values())
    fleiss = (observed-chance_inter)/(1-chance_inter) if chance_inter < 1 else None

    def distance(a, b, ordinal):
        i, j = sorted((LABELS.index(a), LABELS.index(b)))
        if i == j:
            return 0.0
        if not ordinal:
            return float((i-j)**2)
        mass = sum(expert_counts[k] for k in LABELS[i:j+1])
        return (mass-(expert_counts[a]+expert_counts[b])/2)**2

    def alpha(ordinal):
        do = sum(sum(ca*cb*distance(a,b,ordinal) for a,ca in c.items()
                     for b,cb in c.items())/(m-1) for c in counts)/n
        de = sum(ca*cb*distance(a,b,ordinal) for a,ca in expert_counts.items()
                 for b,cb in expert_counts.items())/(n*(n-1))
        return 1-do/de if de else None

    threshold = math.ceil(0.75*m)
    majority = [unit for unit in units.values()
                if max(Counter(r["expert_trace"] for r in unit.values()).values()) >= threshold]
    majority_matches = sum(
        sum(r["expert_trace"] == next(iter(unit.values()))["lemon_trace"] for r in unit.values()) >= threshold
        for unit in majority
    )
    total_weight = sum(float(r["weight"]) for r in ratings)
    return {
        "schema_version": "expert-review-v1", "reviewers": m, "factor_rows": len(units),
        "examples": len({r["example_id"] for r in ratings}), "judgments": n,
        "exact_matches": exact, "exact_agreement": exact/n,
        "wilson_95": wilson(exact,n),
        "wilson_note": "Descriptive binomial interval; repeated judgments are clustered by factor/example, not independent.",
        "weighted_exact_agreement": sum(float(r["weight"]) for r in ratings if r["lemon_trace"] == r["expert_trace"])/total_weight,
        "pooled_cohen_kappa": pooled_kappa, "fleiss_kappa": fleiss,
        "krippendorff_alpha_ordinal": alpha(True),
        "krippendorff_alpha_interval_rank": alpha(False),
        "label_order": LABELS,
        "alpha_definition": "Ordinal uses squared marginal-frequency distances; interval_rank uses squared differences of equally spaced ranks 0..5. Experts only.",
        "majority_threshold": threshold, "majority_rows": len(majority),
        "majority_matches": majority_matches,
        "all_lemon_labels_supported": all(any(r["expert_trace"] == r["lemon_trace"] for r in unit.values()) for unit in units.values()),
        "per_reviewer": {reviewer: sum(r["expert_trace"] == r["lemon_trace"] for r in ratings if r["reviewer_id"] == reviewer) for reviewer in sorted(reviewers)},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--raw-dir", type=Path)
    group.add_argument("--ratings", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("--out must be a new directory")
    if args.raw_dir:
        ratings, manifest = import_exports(list(args.raw_dir.glob("*.csv")))
    else:
        ratings = list(csv.DictReader(io.StringIO(args.ratings.read_text(encoding="utf-8-sig"))))
        manifest = {"schema_version":"expert-import-v1", "ratings_sha256": hashlib.sha256(args.ratings.read_bytes()).hexdigest()}
    report = summarize(ratings)
    args.out.mkdir(parents=True)
    with (args.out/"ratings.csv").open("w",encoding="utf-8",newline="") as stream:
        writer = csv.DictWriter(stream,fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(ratings)
    manifest["normalized_sha256"] = hashlib.sha256((args.out/"ratings.csv").read_bytes()).hexdigest()
    for name, data in (("summary.json",report),("manifest.json",manifest)):
        (args.out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=True,indent=2))


if __name__ == "__main__":
    main()
