"""Compute a vector-space perturbation baseline for graph-text pairs.

The default backend is an offline hashed character n-gram cosine. It is a
reproducible vector-space baseline, not a dense semantic embedding. A dense
sentence-transformer backend can be requested with --backend sentence-transformers
when the optional model dependency and model files are available.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUTS = [
    ROOT / "data" / "processed" / "webnlg_perturbed.jsonl",
    ROOT / "data" / "biomedical" / "perturbed" / "drugprot_perturbed.jsonl",
    ROOT / "data" / "biomedical" / "perturbed" / "bc5cdr_perturbed.jsonl",
]
OUT_JSON = ROOT / "reports" / "embedding_baseline_perturbation.json"
OUT_MD = ROOT / "reports" / "embedding_baseline_perturbation.md"

VARIANT_LABELS = {
    "node_deletion": "Node deletion",
    "edge_deletion": "Edge deletion",
    "argument_swap": "Argument swap",
    "polarity_flip": "Polarity flip",
    "relation_blur": "Relation blur",
}


@dataclass(frozen=True)
class Pair:
    item_id: str
    dataset: str
    variant: str
    original_text: str
    perturbed_text: str


def _read_jsonl(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def load_pairs(paths: Sequence[Path], limit_per_variant: int | None = None) -> list[Pair]:
    counts: dict[str, int] = defaultdict(int)
    pairs: list[Pair] = []
    for path in paths:
        for row in _read_jsonl(path):
            variant = row.get("variant")
            if variant not in VARIANT_LABELS:
                continue
            if limit_per_variant is not None and counts[variant] >= limit_per_variant:
                continue
            original = row.get("original_text") or row.get("text") or ""
            perturbed = row.get("text") or row.get("perturbed_text") or ""
            if not original or not perturbed:
                continue
            pairs.append(
                Pair(
                    item_id=str(row.get("id", "")),
                    dataset=str(row.get("dataset", path.stem)),
                    variant=variant,
                    original_text=original,
                    perturbed_text=perturbed,
                )
            )
            counts[variant] += 1
    return pairs


def _normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    return f" {text} "


def _stable_bucket(token: str, dims: int) -> int:
    digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "little") % dims


def _hashed_char_ngram_vector(text: str, dims: int, min_n: int, max_n: int) -> dict[int, float]:
    text = _normalize_text(text)
    counts: Counter[int] = Counter()
    for n in range(min_n, max_n + 1):
        if len(text) < n:
            continue
        for idx in range(0, len(text) - n + 1):
            ngram = text[idx : idx + n]
            bucket = _stable_bucket(ngram, dims)
            counts[bucket] += 1
    norm = math.sqrt(sum(value * value for value in counts.values()))
    if norm == 0.0:
        return {}
    return {key: value / norm for key, value in counts.items()}


def _sparse_cosine(a: dict[int, float], b: dict[int, float]) -> float:
    if not a or not b:
        return 0.0
    if len(a) > len(b):
        a, b = b, a
    return sum(value * b.get(key, 0.0) for key, value in a.items())


def hash_char_cosines(
    pairs: Sequence[Pair], *, dims: int = 2**18, min_n: int = 3, max_n: int = 5
) -> list[float]:
    """Fast offline vector-space cosine using sklearn when available.

    The function name is kept for CLI/backward compatibility. It uses a
    character n-gram TF-IDF representation with a capped vocabulary. If sklearn
    is unavailable, it falls back to a smaller pure-Python hashed representation.
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
    except Exception:
        scores: list[float] = []
        # Pure-Python fallback. Use at most 4096 characters per side to keep this
        # path usable on machines without sklearn.
        for pair in pairs:
            original_vec = _hashed_char_ngram_vector(
                pair.original_text[:4096], dims, min_n, max_n
            )
            perturbed_vec = _hashed_char_ngram_vector(
                pair.perturbed_text[:4096], dims, min_n, max_n
            )
            scores.append(max(0.0, min(1.0, _sparse_cosine(original_vec, perturbed_vec))))
        return scores

    texts: list[str] = []
    for pair in pairs:
        texts.append(pair.original_text)
        texts.append(pair.perturbed_text)
    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(min_n, max_n),
        lowercase=True,
        strip_accents="unicode",
        max_features=min(dims, 50000),
        norm="l2",
    )
    matrix = vectorizer.fit_transform(texts)
    scores = []
    for idx in range(0, matrix.shape[0], 2):
        cosine = matrix[idx].multiply(matrix[idx + 1]).sum()
        scores.append(max(0.0, min(1.0, float(cosine))))
    return scores

def sentence_transformer_cosines(pairs: Sequence[Pair], model_name: str, batch_size: int) -> list[float]:
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on optional environment
        raise RuntimeError(
            "sentence-transformers is not installed. Install optional research dependencies "
            "or use --backend hash-char."
        ) from exc

    model = SentenceTransformer(model_name)
    originals = [pair.original_text for pair in pairs]
    perturbed = [pair.perturbed_text for pair in pairs]
    original_emb = model.encode(originals, batch_size=batch_size, normalize_embeddings=True)
    perturbed_emb = model.encode(perturbed, batch_size=batch_size, normalize_embeddings=True)
    scores = (original_emb * perturbed_emb).sum(axis=1)
    return [max(0.0, min(1.0, float(score))) for score in scores]


def summarize(pairs: Sequence[Pair], cosines: Sequence[float]) -> dict:
    rows_by_variant: dict[str, list[float]] = defaultdict(list)
    rows_by_dataset_variant: dict[tuple[str, str], list[float]] = defaultdict(list)
    for pair, cosine in zip(pairs, cosines):
        drop = 1.0 - cosine
        rows_by_variant[pair.variant].append(drop)
        rows_by_dataset_variant[(pair.dataset, pair.variant)].append(drop)

    by_variant = []
    for variant, label in VARIANT_LABELS.items():
        drops = rows_by_variant.get(variant, [])
        if not drops:
            continue
        by_variant.append(
            {
                "variant": variant,
                "label": label,
                "n": len(drops),
                "mean_cosine": round(1.0 - mean(drops), 4),
                "mean_drop": round(mean(drops), 4),
                "std_drop": round(pstdev(drops), 4) if len(drops) > 1 else 0.0,
                "min_drop": round(min(drops), 4),
                "max_drop": round(max(drops), 4),
            }
        )

    by_dataset_variant = []
    for (dataset, variant), drops in sorted(rows_by_dataset_variant.items()):
        by_dataset_variant.append(
            {
                "dataset": dataset,
                "variant": variant,
                "label": VARIANT_LABELS.get(variant, variant),
                "n": len(drops),
                "mean_cosine": round(1.0 - mean(drops), 4),
                "mean_drop": round(mean(drops), 4),
            }
        )

    return {"by_variant": by_variant, "by_dataset_variant": by_dataset_variant}


def build_report(args: argparse.Namespace) -> dict:
    input_paths = [Path(path).resolve() for path in args.inputs]
    pairs = load_pairs(input_paths, args.limit_per_variant)
    if not pairs:
        raise SystemExit("No perturbation pairs were loaded.")

    backend = args.backend
    backend_note = ""
    if backend == "hash-char":
        cosines = hash_char_cosines(
            pairs, dims=args.hash_dims, min_n=args.min_ngram, max_n=args.max_ngram
        )
        backend_name = "char_ngram_vector_cosine"
        backend_note = (
            "Offline character n-gram vector cosine. The implementation uses sklearn "
            "TF-IDF when available and a bounded hashed fallback otherwise. This is a "
            "reproducible vector-space baseline, not a dense semantic embedding."
        )
        backend_params = {
            "hash_dims": args.hash_dims,
            "min_ngram": args.min_ngram,
            "max_ngram": args.max_ngram,
        }
    elif backend == "sentence-transformers":
        cosines = sentence_transformer_cosines(pairs, args.model, args.batch_size)
        backend_name = "sentence_transformer_cosine"
        backend_note = "Dense sentence-transformer cosine on original vs perturbed text."
        backend_params = {"model": args.model, "batch_size": args.batch_size}
    else:  # pragma: no cover
        raise ValueError(f"Unknown backend: {backend}")

    summary = summarize(pairs, cosines)
    return {
        "status": "passed",
        "backend": backend_name,
        "backend_note": backend_note,
        "backend_params": backend_params,
        "definition": "mean_drop = 1 - cosine(original_text, perturbed_text); larger means stronger vector-space response to perturbation",
        "input_files": [str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path) for path in input_paths],
        "n_pairs": len(pairs),
        "variants": list(VARIANT_LABELS.keys()),
        **summary,
        "safe_interpretation": (
            "This baseline measures how much vector-space text similarity changes under "
            "controlled perturbations. It is a topical/lexical reference signal unless the "
            "sentence-transformer backend is explicitly used. It should not be read as a "
            "complete comparison against modern dense embeddings."
        ),
        "do_not_claim": [
            "Do not claim that this offline baseline represents all embedding models.",
            "Do not claim global superiority of LEMON-Factor over embeddings from these numbers.",
            "Use dense sentence-transformer results only when the sentence-transformer backend was run.",
        ],
    }


def write_markdown(report: dict, path: Path) -> None:
    lines = [
        "# Vector-space perturbation baseline",
        "",
        f"Status: `{report['status']}`",
        f"Backend: `{report['backend']}`",
        "",
        report["backend_note"],
        "",
        "Definition: `" + report["definition"] + "`",
        "",
        "## Mean drops by perturbation",
        "",
        "| Perturbation | n | Mean cosine | Mean drop | Std drop |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in report["by_variant"]:
        lines.append(
            f"| {row['label']} | {row['n']} | {row['mean_cosine']:.4f} | "
            f"{row['mean_drop']:.4f} | {row['std_drop']:.4f} |"
        )
    lines.extend(
        [
            "",
            "## Safe interpretation",
            "",
            report["safe_interpretation"],
            "",
            "## Do not claim",
            "",
        ]
    )
    for item in report["do_not_claim"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run vector-space baseline on perturbation pairs.")
    parser.add_argument("--backend", choices=["hash-char", "sentence-transformers"], default="hash-char")
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--hash-dims", type=int, default=2**18)
    parser.add_argument("--min-ngram", type=int, default=3)
    parser.add_argument("--max-ngram", type=int, default=5)
    parser.add_argument("--limit-per-variant", type=int, default=None)
    parser.add_argument("--json", type=Path, default=OUT_JSON)
    parser.add_argument("--md", type=Path, default=OUT_MD)
    parser.add_argument("inputs", nargs="*", default=[str(path) for path in DEFAULT_INPUTS])
    args = parser.parse_args()

    report = build_report(args)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, args.md)
    print(f"Wrote {args.json}")
    print(f"Wrote {args.md}")


if __name__ == "__main__":
    main()
