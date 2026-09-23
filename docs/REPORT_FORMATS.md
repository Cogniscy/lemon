# Report formats and compatibility

## Perturbation scoring

New schema: `perturbation-scoring-v2`.
The score formerly called `lemon_full` is now `factor_damage_proxy`.
The numerical formula is unchanged. `proxy_evidence` states that the input is
the factor inventory plus intended-damage metadata, not inference from text.

`normalize_scoring_report` accepts known legacy scoring structure
(input, inventory, rows, summary, metrics) and v2. It migrates row scores,
summary metrics and metric names without mutating the supplied report.
Conflicting old/new values and unknown schema versions raise errors.

Compact sensitivity has a separate `perturbation-sensitivity-v2` adapter.
These are format-specific migrations, not recursive replacement in arbitrary JSON.
Ablation labels identify the damage proxy; the historical internal variant name
`full` remains for compatibility.

## Vector controls

New schema: `vector-baseline-v2`.

| CLI backend | Algorithm | Extra dependency | Fit scope |
|---|---|---|---|
| hashed-char | Hashed character counts, L2 cosine | none | none |
| tfidf-char | Character-within-word TF-IDF cosine | scikit-learn | both sides of selected pairs |
| sentence-transformers | Dense model cosine | sentence-transformers, model files | pretrained model |

Reports record input SHA-256, parameters and library versions. Missing dependencies
raise an error; there is no fallback. The old `hash-char` option errors with
migration guidance because its algorithm depended on installed libraries.

Historical `char_ngram_vector_cosine` alone cannot establish the algorithm.
New plot metadata marks that historical algorithm as `unknown`.
Do not relabel historical numbers as a particular backend without run evidence.

The new pure-Python hashed backend processes full text. The historical fallback
truncated each side at 4096 characters, so reruns are not presumed identical.

## Preserving historical artifacts

Existing reports and binary figures are not overwritten during migration.
New aggregate/plot defaults use `artifacts/`; explicit destinations remain available.
Historical paper table numbers are retained, with corrected proxy labels and
interpretation. Existing PDF files are historical and may not reflect edited TeX.
