"""Run MINE-style node/edge information retention on WebNLG.

The default mode is deterministic. Optional ``--judge llm`` adds an
OpenRouter-based binary fact recoverability judge over retrieved subgraphs,
bringing this WebNLG adaptation closer to KGGen's MINE protocol.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lemon_factor.datasets.unified_io import read_jsonl
from lemon_factor.llm.decompose_predicates import read_model_config
from lemon_factor.mine_nodes_edges.llm_judge import (
    build_judge_payloads,
    read_offline_judgment_fixture,
    run_live_judgments,
    write_jsonl,
)
from lemon_factor.mine_nodes_edges.scoring import (
    MineStyleFactScore,
    apply_fact_judgments,
    build_mine_style_report,
    score_mine_style_corpus,
    write_mine_style_outputs,
)
from lemon_factor.reverse.reconstruct_graph import read_reconstructed_graphs


def _fmt_optional(value: object) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_mine_style_table(report: dict[str, object], path: str | Path) -> None:
    lines = [
        "| Metric | Value |",
        "|---|---:|",
        f"| Examples | {report['examples']} |",
        f"| Facts | {report['facts']} |",
        f"| Node information | {float(report['node_information']):.4f} |",
        f"| Edge information | {float(report['edge_information']):.4f} |",
        f"| Retrieved edge hit rate | {float(report['retrieved_edge_hit_rate']):.4f} |",
        f"| Fact recoverability | {float(report['fact_recoverability']):.4f} |",
        f"| Composite node/edge score | {float(report.get('composite_node_edge_score', report['mine_style_score'])):.4f} |",
        f"| MINE-style score | {float(report['mine_style_score']):.4f} |",
    ]
    if int(report.get("judged_facts", 0)):
        lines.extend(
            [
                f"| Requested judgments | {_fmt_optional(report.get('requested_judgments'))} |",
                f"| Valid judgments | {_fmt_optional(report.get('valid_judgments'))} |",
                f"| Failed judgments | {_fmt_optional(report.get('failed_judgments'))} |",
                f"| Judged facts | {report.get('judged_facts', 0)} |",
                f"| Judge parse success rate | {_fmt_optional(report.get('judge_parse_success_rate'))} |",
                f"| Retry attempts | {_fmt_optional(report.get('retry_attempts'))} |",
                f"| Retry successes | {_fmt_optional(report.get('retry_successes'))} |",
                f"| Judge changed count | {_fmt_optional(report.get('judge_changed_count'))} |",
                f"| Judge agreement with deterministic | {_fmt_optional(report.get('judge_agreement_with_deterministic'))} |",
                f"| Deterministic composite score on same subset | {_fmt_optional(report.get('deterministic_score_on_subset'))} |",
                f"| Deterministic node information on same subset | {_fmt_optional(report.get('deterministic_node_information_on_subset'))} |",
                f"| Deterministic edge information on same subset | {_fmt_optional(report.get('deterministic_edge_information_on_subset'))} |",
                f"| Deterministic fact recoverability on same subset | {_fmt_optional(report.get('deterministic_fact_recoverability_on_subset'))} |",
                f"| LLM fact recoverability | {_fmt_optional(report.get('llm_fact_recoverability'))} |",
                f"| Mean judge confidence | {_fmt_optional(report.get('mean_judge_confidence'))} |",
            ]
        )
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", help="Unified GraphText JSONL")
    parser.add_argument("--reconstructed", required=True, help="Reconstructed graph JSONL")
    parser.add_argument("--out", required=True, help="MINE-style report JSON")
    parser.add_argument("--scores", required=True, help="Fact-level MINE-style scores JSONL")
    parser.add_argument("--table", required=True, help="Markdown table")
    parser.add_argument("--top-k", type=int, default=2, help="Retrieved nodes per fact")
    parser.add_argument("--hops", type=int, default=2, help="Subgraph expansion hops")
    parser.add_argument("--judge", choices=["deterministic", "offline", "llm"], default="deterministic")
    parser.add_argument("--models", help="YAML-like judge model config")
    parser.add_argument("--model", action="append", help="Single judge model id; may be repeated")
    parser.add_argument("--offline-fixture", help="JSONL fixture for --judge offline")
    parser.add_argument("--raw-out", help="Raw judge responses JSONL")
    parser.add_argument("--prompts-out", default="data/interim/mine_style_judge_prompts.jsonl")
    parser.add_argument("--dry-run", action="store_true", help="Write judge prompts instead of calling OpenRouter")
    parser.add_argument("--limit", type=int, default=None, help="Limit facts for deterministic/offline/live judge modes")
    parser.add_argument("--subset-out", help="Write selected fact ids to JSON for locked subset comparison")
    parser.add_argument("--subset-in", help="Read selected fact ids from JSON and score exactly that subset")
    parser.add_argument("--compact-context", action="store_true", help="Compact retrieved subgraph in LLM prompts")
    parser.add_argument("--max-context-nodes", type=int, default=6, help="Maximum retrieved nodes in compact prompt")
    parser.add_argument("--max-context-edges", type=int, default=6, help="Maximum retrieved edges in compact prompt")
    parser.add_argument("--reason-max-words", type=int, default=20, help="Requested maximum judge reason length")
    parser.add_argument("--max-tokens", type=int, default=250, help="OpenRouter max_tokens for judge responses")
    parser.add_argument("--retry-invalid-json", action="store_true", help="Retry invalid JSON once with an ultra-compact prompt")
    return parser


def _resolve_models(args: argparse.Namespace) -> list[str]:
    models: list[str] = []
    if args.models:
        models.extend(read_model_config(args.models))
    if args.model:
        models.extend(args.model)
    if not models:
        models = ["meta-llama/llama-3.1-70b-instruct"]
    return list(dict.fromkeys(models))


def _unique_example_count(scores: list[object]) -> int:
    return len({getattr(score, "example_id") for score in scores})


def _read_subset(path: str | Path) -> list[str]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        ids = payload.get("fact_ids", [])
    else:
        ids = payload
    if not isinstance(ids, list):
        raise ValueError("Subset file must contain a list or {'fact_ids': [...]} object")
    return [str(item) for item in ids]


def _write_subset(path: str | Path, scores: list[MineStyleFactScore]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "fact_ids": [score.fact_id for score in scores],
        "count": len(scores),
        "description": "Locked fact subset for deterministic and LLM-judged MINE-style comparison.",
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _select_scores(scores: list[MineStyleFactScore], *, limit: int | None = None, subset_ids: list[str] | None = None) -> list[MineStyleFactScore]:
    if subset_ids is not None:
        by_id = {score.fact_id: score for score in scores}
        missing = [fact_id for fact_id in subset_ids if fact_id not in by_id]
        if missing:
            raise ValueError(f"Subset contains unknown fact ids: {missing[:5]}")
        return [by_id[fact_id] for fact_id in subset_ids]
    return scores[:limit] if limit is not None else scores


def _retry_stats(raw_records: list[dict]) -> tuple[int, int]:
    retry_attempts = sum(1 for record in raw_records if int(record.get("attempt", 1)) > 1)
    retry_successes = sum(1 for record in raw_records if record.get("retry_success") is True)
    return retry_attempts, retry_successes


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    examples = read_jsonl(args.jsonl)
    records = read_reconstructed_graphs(args.reconstructed)
    _full_report, deterministic_scores = score_mine_style_corpus(examples, records, top_k=args.top_k, hops=args.hops)

    subset_ids = _read_subset(args.subset_in) if args.subset_in else None
    selected_scores = _select_scores(deterministic_scores, limit=args.limit, subset_ids=subset_ids)
    if args.subset_out:
        _write_subset(args.subset_out, selected_scores)

    if args.judge == "deterministic":
        report = build_mine_style_report(
            selected_scores,
            examples=_unique_example_count(selected_scores),
            top_k=args.top_k,
            hops=args.hops,
            judge_mode="deterministic",
        )
        write_mine_style_outputs(report, selected_scores, out=args.out, scores_path=args.scores)
        write_mine_style_table(report.model_dump(mode="json"), args.table)
        print(json.dumps({"out": args.out, "scores": args.scores, "table": args.table, "subset_out": args.subset_out}, indent=2))
        return

    models = _resolve_models(args)
    raw_records: list[dict] = []

    if args.dry_run:
        prompt_records = build_judge_payloads(
            selected_scores,
            models=models,
            limit=None,
            compact_context=args.compact_context,
            max_context_nodes=args.max_context_nodes,
            max_context_edges=args.max_context_edges,
            reason_max_words=args.reason_max_words,
            max_tokens=args.max_tokens,
        )
        write_jsonl(args.prompts_out, prompt_records)
        print(json.dumps({"prompts": args.prompts_out, "records": len(prompt_records), "subset_out": args.subset_out}, indent=2))
        return

    if args.judge == "offline":
        if not args.offline_fixture:
            raise SystemExit("--judge offline requires --offline-fixture")
        judgments, raw_records = read_offline_judgment_fixture(args.offline_fixture)
    else:
        prompt_records = build_judge_payloads(
            selected_scores,
            models=models,
            limit=None,
            compact_context=args.compact_context,
            max_context_nodes=args.max_context_nodes,
            max_context_edges=args.max_context_edges,
            reason_max_words=args.reason_max_words,
            max_tokens=args.max_tokens,
        )
        judgments, raw_records = run_live_judgments(prompt_records, retry_invalid_json=args.retry_invalid_json)

    judged_scores = apply_fact_judgments(selected_scores, judgments, judge_mode=args.judge)
    parsed_count = sum(1 for record in raw_records if record.get("parsed"))
    requested = len(raw_records)
    parse_success_rate = round(parsed_count / requested, 6) if requested else 0.0
    retry_attempts, retry_successes = _retry_stats(raw_records)
    report = build_mine_style_report(
        judged_scores,
        examples=_unique_example_count(judged_scores),
        top_k=args.top_k,
        hops=args.hops,
        judge_mode=args.judge,
        parse_success_rate=parse_success_rate,
        models=models,
        requested_judgments=requested,
        failed_judgments=max(requested - parsed_count, 0),
        retry_attempts=retry_attempts,
        retry_successes=retry_successes,
        deterministic_scores=selected_scores,
    )
    write_mine_style_outputs(report, judged_scores, out=args.out, scores_path=args.scores)
    write_mine_style_table(report.model_dump(mode="json"), args.table)
    if args.raw_out:
        write_jsonl(args.raw_out, raw_records)
    print(
        json.dumps(
            {"out": args.out, "scores": args.scores, "raw_out": args.raw_out, "table": args.table, "subset_out": args.subset_out},
            indent=2,
        )
    )


if __name__ == "__main__":  # pragma: no cover
    main()
