| Method | Direction | Factors | Retrieval | LLM judge | Score | Diagnostic level |
|---|---|---:|---:|---:|---:|---|
| Forward LEMON-Factor | KG→Text | yes | no | no | 0.7915 | factor/edge/example/corpus |
| Reverse LEMON-Factor | Text→KG | yes | no | no | 0.7789 | factor/edge/example/corpus |
| MINE-style nodes/edges | Text→KG | no | yes | no | 0.8028 | node/edge/fact/corpus |
| MINE-style nodes/edges + LLM judge | Text→KG | no | yes | yes | 0.2857 | node/edge/fact/corpus |
| Graph-text token cosine | KG↔Text | no | no | no | 0.7357 | corpus |
| Graph-text token Jaccard | KG↔Text | no | no | no | 0.6233 | corpus |
