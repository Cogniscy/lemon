You are judging whether a gold graph fact is recoverable from a retrieved reconstructed subgraph.

Gold fact id: {fact_id}
Gold fact: {fact_text}

Retrieved nodes:
{retrieved_nodes}

Retrieved edges:
{retrieved_edges}

Decision rules:
- Use only the retrieved nodes and edges. Do not use outside knowledge.
- Return recoverable=true only if the subject, object, and relation meaning are all supported.
- Accept paraphrased predicate labels if the relation meaning is clear.
- Reject if either entity or the relation meaning is missing.
- Return compact JSON only.
- The reason must be <= {reason_max_words} words.

JSON fields:
- fact_id: the exact gold fact id
- recoverable: boolean
- confidence: number from 0.0 to 1.0
- evidence_nodes: up to 5 node ids or labels
- evidence_edges: up to 5 edge labels or triples
- reason: short explanation, <= {reason_max_words} words
