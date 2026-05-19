# Integration notes for the LEMON-Factor research brief

The uploaded research brief is used to populate the paper skeleton rather than copied verbatim.

Key adopted points:

1. LEMON-Factor differs from holistic metrics by producing predicate-factor-level audit trails.
2. FactSpotter is the closest graph-to-text factuality baseline, but it remains binary at triple level.
3. FActScore and VERISCORE decompose generated text into claims, while LEMON-Factor decomposes source predicates.
4. FrameNet, PropBank, VerbNet, AMR, and Neo-Davidsonian semantics motivate role-aware predicate decomposition.
5. Synthetic LLM adjudication must be described as a bootstrap and not as human expert validation.

Paper placement:

- `paper/sections/01_introduction.tex`: problem, gap, method, contributions.
- `paper/sections/02_related_work.tex`: benchmark/metric map.
- `paper/sections/08_limitations.tex`: LLM-as-judge limitation.
- `paper/references.bib`: initial BibTeX entries.
