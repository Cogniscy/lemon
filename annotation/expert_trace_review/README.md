# Pilot expert trace review

Four completed CSV exports supplied by the project owner contain 35 factor rows
over eight examples per reviewer (140 judgments). A fifth empty template was excluded.
The original exports encoded record separators as literal backslash-n.
Import repairs separators outside quoted fields and converts Russian labels to
the declared English scale. Original exports remain unchanged outside the repository.

Files:

- ratings.csv: aligned, anonymized ratings and source example/factor metadata.
- summary.json: recomputed agreement measures.
- manifest.json: hashes of original bytes and normalized ratings; original filenames
  and reviewer identifiers are omitted.

Reviewer IDs are R1–R4. Comments, confidence and severity columns are omitted because
they are not used in the reported calculations. Source labels and weights are preserved.

Recompute from the distributable ratings:

```bash
python -m lemon_factor.analysis.expert_review --ratings annotation/expert_trace_review/ratings.csv --out artifacts/expert-recomputed
```

The output directory must not already exist. To import the original exports, use
`--raw-dir PATH` instead of `--ratings`.

## Results and correction

- Exact agreement: 119/140 = 85.0%.
- Factor-weighted exact agreement: 85.78125%.
- Pooled Cohen kappa: 0.7906579322.
- Fleiss inter-expert kappa: 0.6889790399.
- Krippendorff ordinal alpha: 0.8726722592 (rounds to 0.873).
- Krippendorff interval alpha on equally spaced ranks: 0.8710995016.
- At least 3/4 agreement on 28 rows; LEMON matches 27 majorities.

The manuscript formerly called 0.871 an ordinal alpha. That value is reproduced
using equally spaced ranks, not the marginal-frequency ordinal distance.
The revised manuscript reports ordinal alpha 0.873 and documents the scale.

Order: contradicted < lost < mostly_lost < partial < mostly_preserved < preserved.
Ordinal distances use pooled expert category frequencies; alpha excludes LEMON.
Cohen kappa pools all LEMON/expert pairs; it is not the mean of reviewer kappas.
The descriptive Wilson interval treats 140 decisions as binomial observations;
because reviewers assess shared factors/examples, it is not a cluster-adjusted interval.

Formula cross-check reference:
[fast-krippendorff source](https://github.com/pln-fing-udelar/fast-krippendorff/blob/master/krippendorff/krippendorff.py).
