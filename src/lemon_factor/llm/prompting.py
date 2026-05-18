"""Prompt construction for LLM predicate decomposition candidates."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from lemon_factor.factors.decomposition import SemanticFactor
from lemon_factor.factors.inventory import PredicateInventoryItem

PROMPT_PATH = Path(__file__).parent / "prompts" / "decompose_predicate.md"


def factor_schema_brief(factors: list[SemanticFactor]) -> str:
    """Return a compact factor schema description for prompts."""

    lines = []
    for factor in factors:
        roles = ", ".join(factor.allowed_roles)
        lines.append(f"- {factor.id}: {factor.description} Allowed roles: {roles}.")
    return "\n".join(lines)


def predicate_context_brief(item: PredicateInventoryItem, *, max_examples: int = 3) -> str:
    """Return examples and evidence for one predicate."""

    categories = ", ".join(f"{k}:{v}" for k, v in sorted(item.categories.items()))
    candidates = ", ".join(item.candidate_factors)
    examples = []
    for example in item.examples[:max_examples]:
        examples.append(f"- {example.get('subj')} -- {example.get('pred')} -- {example.get('obj')}")
        text = example.get("text")
        if text:
            examples.append(f"  Text: {text}")
    return dedent(
        f"""
        Predicate: {item.predicate}
        Count in train inventory: {item.count}
        Categories: {categories}
        Candidate lexical factors: {candidates}
        Examples:
        {chr(10).join(examples)}
        """
    ).strip()


def load_prompt_template(path: str | Path | None = None) -> str:
    template_path = Path(path) if path else PROMPT_PATH
    return template_path.read_text(encoding="utf-8")


def render_decomposition_prompt(
    item: PredicateInventoryItem,
    factors: list[SemanticFactor],
    *,
    template: str | None = None,
) -> str:
    """Render a prompt for one predicate."""

    template = template if template is not None else load_prompt_template()
    return template.format(
        predicate=item.predicate,
        predicate_context=predicate_context_brief(item),
        factor_schema=factor_schema_brief(factors),
    )


def build_messages(prompt: str) -> list[dict[str, str]]:
    """Build chat messages for OpenRouter."""

    return [
        {
            "role": "system",
            "content": (
                "You generate candidate semantic decompositions for graph predicates. "
                "You must follow the supplied JSON schema and use only allowed factors."
            ),
        },
        {"role": "user", "content": prompt},
    ]
