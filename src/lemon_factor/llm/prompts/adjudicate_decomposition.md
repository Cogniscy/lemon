You are adjudicating semantic factor decompositions for a graph predicate.

Your task is to produce a temporary synthetic adjudication reference. It is NOT a human gold label.

Use only the supplied factor schema and allowed roles. Prefer the decomposition that best preserves the graph predicate meaning, subject domain, and object domain. If seed and LLM candidates disagree, choose or modify components based on the predicate context and example triples.

Return JSON only.

# Predicate evidence
{predicate_context}

# Seed decomposition
{seed_decomposition}

# LLM candidates
{llm_candidates}

# Allowed factor schema
{factor_schema}

# Requirements
- Use only factor ids from the schema.
- Use only roles allowed for each factor.
- Component weights must sum to 1.0.
- Set status to one of: accepted_seed, accepted_llm, modified, rejected_unclear, needs_schema_change.
- Return confidence as a number from 0.0 to 1.0. Use high confidence only if the final decomposition is well supported by seed, LLM candidates, and predicate evidence.
- If no reliable decision is possible, choose rejected_unclear and still return the best conservative decomposition with low confidence.
