# Reference Sources for the SPECOM-Oriented Pilot

This file lists the external resources that motivate the project design. Keep it updated with exact versions, URLs, and dataset snapshots when lemon-02 starts.

## SPECOM

- SPECOM 2026 website: https://specom.nw.ru/
- Full papers are expected in Springer LNCS style, 10–15 pages, with independent peer review and publication in LNCS/LNAI proceedings.

## WebNLG

- Hugging Face dataset card: https://huggingface.co/datasets/GEM/web_nlg
- GEM dataset card: https://gem-benchmark.com/data_cards/web_nlg
- Challenge description: https://synalp.gitlabpages.inria.fr/webnlg-challenge/

Use in this project:

- clean graph/text benchmark;
- explicit DBpedia triples;
- English/Russian texts;
- useful for graph-text semantic preservation without extraction.

## BioRED

- NCBI GitHub repository: https://github.com/ncbi/BioRED
- PubMed paper: https://pubmed.ncbi.nlm.nih.gov/35849818/

Use in this project:

- biomedical document-level relations;
- entity types such as gene/protein, disease, chemical;
- train/development/test split;
- novelty/background relation labels.

## MINE / KGGen

- KGGen paper: https://arxiv.org/html/2502.09956v2
- KGGen repository: https://github.com/stair-lab/kg-gen

Use in this project:

- fact recoverability baseline;
- fact embeddings and KG node retrieval;
- 2-hop subgraph expansion;
- binary LLM-as-judge inferability.

## Sentence embeddings

- `sentence-transformers/all-MiniLM-L6-v2`: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2

Use in this project:

- intended embedding model for MINE-compatible retrieval and embedding baseline.

## Notes for future reproducibility

When lemon-02 begins, record:

- exact dataset versions or commit hashes;
- download dates;
- license/access restrictions;
- preprocessing commands;
- generated checksum for processed JSONL files.
