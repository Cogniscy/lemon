# LEM-01 Contribution Contract

This file fixes the contributions for the final SPECOM paper. Each contribution is narrow enough to defend in review and broad enough to connect the WebNLG and biomedical experiments.

## Final contribution list

1. **Predicate-factor formulation.** We define a source-driven representation in which each graph predicate is decomposed into typed semantic factors such as participant roles, entity-type constraints, directionality, polarity, relation class, and evidence form.

2. **Bidirectional graph--text evaluation.** We use the same factor representation for forward coverage, where a text is checked against a source graph, and reverse recoverability, where graph factors are checked against information recovered from text.

3. **Cross-domain instantiation.** We instantiate the framework for WebNLG and for two biomedical relation datasets, DrugProt and BC5CDR. The biomedical experiments are transfer diagnostics, not biomedical relation extraction leaderboards.

4. **Controlled diagnostics and ablations.** We compare LEMON-Factor with entity overlap, binary triple or relation checks, and a MINE-style node/edge baseline under perturbations that remove nodes, remove edges, swap arguments, flip polarity, or blur relation meaning.

5. **Synthetic reliability checks.** We report multi-model agreement for model-produced decompositions and model-judged factor coverage. This is presented as reliability evidence for a pilot resource, not as human expert validation.

## Contribution-to-section mapping

| Contribution | Main section | Required result |
|---|---|---|
| Predicate-factor formulation | Method | Formal definition + Figure 1A |
| Bidirectional evaluation | Method / Results | Forward/Reverse table + Figure 1B |
| Cross-domain instantiation | Data / Results | Dataset table + biomedical transfer table |
| Controlled diagnostics and ablations | Experiments / Results | Perturbation table + ablation table |
| Synthetic reliability checks | Data / Limitations / Results | LLM reliability table + limitations paragraph |

## Writing constraints

- Use "we define", "we instantiate", and "we evaluate" for supported actions.
- Use "we find" only for reported results.
- Use "we suggest" or "the results support" for interpretation.
- Avoid broad phrases such as "solves", "fully captures", "human-like", "universal", and "state of the art".
- Keep the vocabulary clear and technical; avoid decorative wording.
