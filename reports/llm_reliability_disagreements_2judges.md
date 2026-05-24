# LLM reliability disagreement examples

## web_nlg_en-validation-524::perturb::node_deletion
Dataset: `webnlg`; variant: `node_deletion`.
Edge: `Albany, Oregon --isPartOf--> Oregon`.

| Factor | Votes |
|---|---|
| location_relation::modifier | partial, covered |
| place::subject_domain | absent, partial |

## drugprot::train::10864881::perturb::node_deletion
Dataset: `drugprot`; variant: `node_deletion`.
Edge: `Betaxolol --chemical_antagonist_of_gene_or_protein--> beta(1)-adrenoceptor`.

| Factor | Votes |
|---|---|
| gene_or_protein::object_domain | partial, covered |
| antagonist_relation::predicate_meaning | partial, covered |
| negative_polarity::modifier | partial, covered |

## bc5cdr::train::18503483::perturb::node_deletion
Dataset: `bc5cdr`; variant: `node_deletion`.
Edge: `tacrolimus --chemical_disease_interaction--> brachial neuritis`.

| Factor | Votes |
|---|---|
| disease::object_domain | absent, covered |
| chemical_induced_disease_relation::predicate_meaning | absent, covered |
| causal_polarity::modifier | absent, covered |
| document_level_evidence::modifier | absent, covered |
| chemical_to_disease_direction::modifier | absent, covered |
