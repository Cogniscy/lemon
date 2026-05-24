from __future__ import annotations

import json
from pathlib import Path

from lemon_factor.reliability.summarize_llm_probe import summarize


def _write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_summarizer_excludes_mock_by_default(tmp_path: Path) -> None:
    items = tmp_path / "items.jsonl"
    judgments = tmp_path / "judgments.jsonl"
    _write(
        items,
        [
            {
                "id": "item-1",
                "dataset": "webnlg",
                "variant": "node_deletion",
                "source_edge": {"subject": "A", "predicate": "p", "object": "B"},
                "original_text": "A p B.",
                "perturbed_text": "A p B.",
                "factors": [{"id": "f1", "label": "F1", "role": "role", "group": "participant_roles", "weight": 1.0}],
            }
        ],
    )
    _write(
        judgments,
        [
            {"item_id": "item-1", "judge_id": "mock_strict", "decisions": [{"factor_id": "f1", "decision": "absent"}]},
            {"item_id": "item-1", "judge_id": "real_judge", "decisions": [{"factor_id": "f1", "decision": "covered"}], "metadata": {"transport": "openrouter"}},
        ],
    )
    report = summarize(items, [str(judgments)])
    assert report["judgment_count"] == 1
    assert report["judge_count"] == 1
    assert report["include_mock"] is False
    assert report["summary"][0]["mean_llm_score"] == 1.0


def test_summarizer_can_include_mock(tmp_path: Path) -> None:
    items = tmp_path / "items.jsonl"
    judgments = tmp_path / "judgments.jsonl"
    _write(
        items,
        [
            {
                "id": "item-1",
                "dataset": "webnlg",
                "variant": "node_deletion",
                "source_edge": {"subject": "A", "predicate": "p", "object": "B"},
                "original_text": "A p B.",
                "perturbed_text": "A p B.",
                "factors": [{"id": "f1", "label": "F1", "role": "role", "group": "participant_roles", "weight": 1.0}],
            }
        ],
    )
    _write(
        judgments,
        [
            {"item_id": "item-1", "judge_id": "mock_strict", "decisions": [{"factor_id": "f1", "decision": "absent"}]},
            {"item_id": "item-1", "judge_id": "real_judge", "decisions": [{"factor_id": "f1", "decision": "covered"}], "metadata": {"transport": "openrouter"}},
        ],
    )
    report = summarize(items, [str(judgments)], include_mock=True)
    assert report["judgment_count"] == 2
    assert report["judge_count"] == 2
    assert report["include_mock"] is True
