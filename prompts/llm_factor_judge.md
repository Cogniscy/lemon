# LEMON-Factor LLM reliability judge prompt

You are judging whether semantic factors from a source graph edge are still supported by a perturbed text.

Use the source edge and the factor list as the reference. Compare the **perturbed text** against that reference. The original text is provided only for context.

For each factor, output exactly one decision:

- `covered`: the perturbed text clearly supports the factor.
- `partial`: the perturbed text weakly or ambiguously supports the factor.
- `absent`: the perturbed text does not support the factor or contradicts it.

Do not infer facts from outside knowledge. Do not reward fluent text if it no longer supports the factor. Keep evidence short: quote only the phrase that supports your decision, or use `null`.

Return **JSON only** using this shape:

```json
{
  "item_id": "...",
  "judge_id": "<model-or-prompt-id>",
  "decisions": [
    {
      "factor_id": "...",
      "decision": "covered|partial|absent",
      "confidence": 0.0,
      "evidence": "short phrase or null"
    }
  ],
  "notes": "optional short note"
}
```

Input item:

```json
<PASTE_ONE_PROMPT_PAYLOAD_HERE>
```
