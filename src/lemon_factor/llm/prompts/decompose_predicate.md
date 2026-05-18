You are helping build LEMON-Factor, a graph-text meaning preservation metric.

Task: decompose the graph predicate `{predicate}` into weighted semantic factors.

Predicate evidence:
{predicate_context}

Allowed semantic factors and roles:
{factor_schema}

Rules:
- Use only factors from the allowed semantic factor list.
- Use only roles allowed for each selected factor.
- Return exactly one JSON object.
- Weights must sum to 1.0.
- Prefer 2-4 components.
- The relation meaning should usually receive the largest weight.
- Do not invent new factors.
- If the predicate is broad, use `entity_relation` with confidence below 0.6.

Required JSON shape:
{{
  "predicate": "{predicate}",
  "components": [
    {{"factor": "...", "role": "...", "weight": 0.0, "rationale": "..."}}
  ],
  "confidence": 0.0,
  "rationale": "short reason for the decomposition"
}}
