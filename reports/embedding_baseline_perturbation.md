# Vector-space perturbation baseline

Status: `passed`
Backend: `char_ngram_vector_cosine`

Offline character n-gram vector cosine. The implementation uses sklearn TF-IDF when available and a bounded hashed fallback otherwise. This is a reproducible vector-space baseline, not a dense semantic embedding.

Definition: `mean_drop = 1 - cosine(original_text, perturbed_text); larger means stronger vector-space response to perturbation`

## Mean drops by perturbation

| Perturbation | n | Mean cosine | Mean drop | Std drop |
|---|---:|---:|---:|---:|
| Node deletion | 1009 | 0.9855 | 0.0145 | 0.0455 |
| Edge deletion | 1009 | 0.9965 | 0.0035 | 0.0164 |
| Argument swap | 1009 | 0.9961 | 0.0039 | 0.0167 |
| Polarity flip | 1009 | 0.9988 | 0.0012 | 0.0021 |
| Relation blur | 1009 | 0.9951 | 0.0049 | 0.0210 |

## Safe interpretation

This baseline measures how much vector-space text similarity changes under controlled perturbations. It is a topical/lexical reference signal unless the sentence-transformer backend is explicitly used. It should not be read as a complete comparison against modern dense embeddings.

## Do not claim

- Do not claim that this offline baseline represents all embedding models.
- Do not claim global superiority of LEMON-Factor over embeddings from these numbers.
- Use dense sentence-transformer results only when the sentence-transformer backend was run.
