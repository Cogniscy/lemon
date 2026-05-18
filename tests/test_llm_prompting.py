from __future__ import annotations

from lemon_factor.factors.inventory import PredicateInventoryItem
from lemon_factor.factors.seed_schema import build_default_factor_schema
from lemon_factor.llm.prompting import build_messages, render_decomposition_prompt


def test_render_decomposition_prompt_contains_schema_and_context():
    item = PredicateInventoryItem(
        predicate="birthPlace",
        count=3,
        categories={"Astronaut": 2},
        candidate_factors=["birth", "place"],
        examples=[{"subj": "A", "pred": "birthPlace", "obj": "B", "text": "A was born in B."}],
    )
    prompt = render_decomposition_prompt(item, build_default_factor_schema())
    assert "birthPlace" in prompt
    assert "biographical_relation" in prompt
    assert "A -- birthPlace -- B" in prompt


def test_build_messages_uses_system_and_user():
    messages = build_messages("hello")
    assert [m["role"] for m in messages] == ["system", "user"]
    assert messages[1]["content"] == "hello"
