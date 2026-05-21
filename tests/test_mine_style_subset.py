import json

from lemon_factor.mine_nodes_edges.run_mine_style import main as run_mine_style
from lemon_factor.reverse.reconstruct_graph import reconstruct_example_graph, write_reconstructed_graphs
from lemon_factor.schema.graphtext import Edge, GraphTextExample, Node, Split
from lemon_factor.datasets.unified_io import write_jsonl


def make_examples():
    return [
        GraphTextExample(
            id="ex1",
            dataset="toy",
            split=Split.dev,
            text="Alan Bean was born in Wheeler, Texas.",
            nodes=[Node(id="s", label="Alan Bean"), Node(id="o", label="Wheeler, Texas")],
            edges=[Edge(subj="s", pred="birthPlace", obj="o")],
        ),
        GraphTextExample(
            id="ex2",
            dataset="toy",
            split=Split.dev,
            text="A book was written by Alice.",
            nodes=[Node(id="s", label="A book"), Node(id="o", label="Alice")],
            edges=[Edge(subj="s", pred="author", obj="o")],
        ),
    ]


def write_inputs(tmp_path):
    examples = make_examples()
    data = tmp_path / "data.jsonl"
    recon = tmp_path / "recon.jsonl"
    write_jsonl(data, examples)
    records = [reconstruct_example_graph(ex, lexical_cues={"birthPlace": ["born in"], "author": ["written by"]}) for ex in examples]
    write_reconstructed_graphs(records, recon)
    return data, recon


def test_subset_out_and_subset_in_use_same_fact_ids(tmp_path):
    data, recon = write_inputs(tmp_path)
    subset = tmp_path / "subset.json"
    out = tmp_path / "det.json"
    scores = tmp_path / "det_scores.jsonl"
    table = tmp_path / "det.md"
    run_mine_style([
        str(data),
        "--reconstructed", str(recon),
        "--judge", "deterministic",
        "--out", str(out),
        "--scores", str(scores),
        "--table", str(table),
        "--subset-out", str(subset),
        "--limit", "1",
    ])
    subset_payload = json.loads(subset.read_text(encoding="utf-8"))
    assert subset_payload["fact_ids"] == ["ex1::edge-0"]
    assert json.loads(out.read_text(encoding="utf-8"))["facts"] == 1

    out2 = tmp_path / "det2.json"
    scores2 = tmp_path / "det2_scores.jsonl"
    table2 = tmp_path / "det2.md"
    run_mine_style([
        str(data),
        "--reconstructed", str(recon),
        "--judge", "deterministic",
        "--out", str(out2),
        "--scores", str(scores2),
        "--table", str(table2),
        "--subset-in", str(subset),
    ])
    lines = scores2.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["fact_id"] == "ex1::edge-0"


def test_dry_run_writes_compact_prompts_and_subset(tmp_path):
    data, recon = write_inputs(tmp_path)
    subset = tmp_path / "subset.json"
    prompts = tmp_path / "prompts.jsonl"
    run_mine_style([
        str(data),
        "--reconstructed", str(recon),
        "--judge", "llm",
        "--dry-run",
        "--out", str(tmp_path / "out.json"),
        "--scores", str(tmp_path / "scores.jsonl"),
        "--table", str(tmp_path / "table.md"),
        "--prompts-out", str(prompts),
        "--subset-out", str(subset),
        "--limit", "1",
        "--compact-context",
        "--max-context-nodes", "1",
        "--max-context-edges", "1",
        "--reason-max-words", "10",
        "--max-tokens", "111",
    ])
    prompt_record = json.loads(prompts.read_text(encoding="utf-8").strip().splitlines()[0])
    assert "<= 10 words" in prompt_record["prompt"]
    assert prompt_record["payload"]["max_tokens"] == 111
    assert json.loads(subset.read_text(encoding="utf-8"))["count"] == 1
