# Perplexity Deep Research prompt: LEMON-Factor related work and introduction

Investigate literature for a paper on **LEMON-Factor: interpretable factor-level graph–text semantic coverage evaluation**. The method evaluates whether a text preserves the meaning of an explicit knowledge graph by decomposing graph predicates into weighted semantic factors and checking factor-level coverage in text.

Please produce a research brief with citations and BibTeX-ready references. Prioritize peer-reviewed papers, official dataset/task pages, and widely used benchmark documentation.

## Research questions

1. **Graph-to-text and RDF-to-text evaluation**
   - Summarize WebNLG and related RDF/KG-to-text tasks.
   - Identify standard metrics used in WebNLG and KG-to-text generation: BLEU, METEOR, chrF++, TER, BERTScore, BLEURT, human data coverage/relevance.
   - Explain why surface/reference metrics may fail to diagnose relation-level semantic omissions or paraphrases.

2. **Semantic faithfulness and data coverage in data-to-text / KG-to-text**
   - Find methods that evaluate whether generated text preserves source table/triple/graph facts.
   - Include works on omissions, additions/hallucinations, data coverage, relation preservation, fact consistency, and semantic adequacy.
   - Explain how LEMON-Factor differs: it scores weighted semantic components rather than full triple exact match or sentence similarity.

3. **Text-to-graph / semantic parsing evaluation**
   - Review triple F1, partial triple matching, entity/relation F1, AMR Smatch, graph similarity, and semantic parsing metrics.
   - Identify ideas useful for evaluating graph–text meaning preservation without performing extraction as the main task.

4. **Semantic decomposition and interpretable representations**
   - Review relevant work on semantic primitives, FrameNet, semantic roles, AMR, conceptual decomposition, interpretable/sparse semantic representations, and ontology-based decomposition.
   - Explain which ideas justify decomposing predicates into role-aware factors.

5. **LLM-assisted annotation / LLM-as-a-judge caveats**
   - Find work on LLM-as-a-judge, synthetic annotation, and known biases.
   - Explain how to phrase a paper limitation when a strong LLM temporarily adjudicates predicate decompositions instead of human experts.

6. **Positioning for SPECOM/NLP paper**
   - Suggest a concise introduction structure: problem, gap, proposed method, contributions, pilot setup, limitations.
   - Suggest 4–6 related work subsections.
   - Suggest 3–5 defensible claims and 3–5 claims to avoid.

## Required output format

1. Executive summary, 500–700 words.
2. Related work map as a table:
   - line of work;
   - representative papers/resources;
   - what they measure;
   - limitation for our problem;
   - how LEMON-Factor complements it.
3. Annotated bibliography with 15–25 entries.
4. Suggested introduction outline.
5. Suggested related work outline.
6. Draft paragraph explaining LEMON-Factor novelty without overclaiming.
7. Draft limitations paragraph for synthetic LLM adjudication.
8. BibTeX entries or at least stable citation metadata.

Important: distinguish clearly between **human gold**, **seed/rule-based reference**, and **synthetic LLM-adjudicated reference**. Do not describe LLM adjudication as expert validation.
