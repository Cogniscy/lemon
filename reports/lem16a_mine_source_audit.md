# LEM-16A MINE source audit

MINE is introduced with KGGen as a benchmark for measuring how much information from text is preserved in an extracted knowledge graph. The MINE-1 procedure uses reference facts, retrieves semantically similar graph nodes, expands the selected nodes to a two-hop subgraph, and asks a binary judge whether the fact can be inferred from the induced subgraph. The reported MINE-1 score is the percentage of binary fact checks scored as recoverable, averaged across articles.

Implementation boundary for this patch:

- We do not vendor KGGen code.
- We do not claim a full MINE reproduction.
- We implement a local MINE-1-compatible baseline: fact query, node retrieval, two-hop subgraph, binary recoverability score, and mean aggregation.
- The deterministic `lexical` mode is for smoke tests and Lemon perturbation diagnostics.
- A later LEM-16B patch may add OpenRouter LLM judging over the same prepared MINE-like items.

Main external references to cite in the paper if this is integrated:

- KGGen paper / MINE description: arXiv 2502.09956.
- Public KGGen repository: `stair-lab/kg-gen`.
- Public MINE evaluation dataset release: `josancamon/kg-gen-MINE-evaluation-dataset`.
