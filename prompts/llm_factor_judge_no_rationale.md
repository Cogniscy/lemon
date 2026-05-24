# LEMON-Factor LLM reliability judge prompt, no rationale condition

Decide whether each semantic factor from the source graph edge is supported by the perturbed text.

Labels:
- `covered`: clearly supported.
- `partial`: weakly or ambiguously supported.
- `absent`: unsupported or contradicted.

Use no outside knowledge. Return JSON only. Set `evidence` to `null` for every factor.

```json
<PASTE_ONE_PROMPT_PAYLOAD_HERE>
```
