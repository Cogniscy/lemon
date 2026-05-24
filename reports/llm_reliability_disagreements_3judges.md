# LLM reliability disagreement examples

## web_nlg_en-validation-524::perturb::node_deletion
Dataset: `webnlg`; variant: `node_deletion`.
Edge: `Albany, Oregon --isPartOf--> Oregon`.

| Factor | Votes |
|---|---|
| part_whole_relation::predicate_meaning | absent, absent, partial |
| location_relation::modifier | partial, covered, partial |
| place::subject_domain | absent, partial, absent |

## web_nlg_en-validation-1657::perturb::argument_swap
Dataset: `webnlg`; variant: `argument_swap`.
Edge: `Hypermarcas --industry--> Pharmaceuticals`.

| Factor | Votes |
|---|---|
| entity_relation::predicate_meaning | covered, covered, absent |
| entity::object_domain | covered, covered, absent |

## drugprot::train::12517247::perturb::polarity_flip
Dataset: `drugprot`; variant: `polarity_flip`.
Edge: `eprosartan --chemical_inhibits_gene_or_protein--> AII`.

| Factor | Votes |
|---|---|
| inhibition_relation::predicate_meaning | covered, covered, partial |
| negative_polarity::modifier | covered, covered, absent |

## drugprot::train::10864881::perturb::node_deletion
Dataset: `drugprot`; variant: `node_deletion`.
Edge: `Betaxolol --chemical_antagonist_of_gene_or_protein--> beta(1)-adrenoceptor`.

| Factor | Votes |
|---|---|
| gene_or_protein::object_domain | partial, covered, partial |
| antagonist_relation::predicate_meaning | partial, covered, covered |
| negative_polarity::modifier | partial, covered, covered |

## drugprot::train::12416991::perturb::edge_deletion
Dataset: `drugprot`; variant: `edge_deletion`.
Edge: `allopregnanolone --chemical_product_of_gene_or_protein--> human 3 alpha-hydroxysteroid dehydrogenase type III`.

| Factor | Votes |
|---|---|
| product_relation::predicate_meaning | covered, covered, partial |
| chemical_to_gene_or_protein_direction::modifier | covered, covered, partial |
| direct_evidence::modifier | covered, covered, partial |

## bc5cdr::train::11027905::perturb::edge_deletion
Dataset: `bc5cdr`; variant: `edge_deletion`.
Edge: `ketamine --chemical_disease_interaction--> Hallucinations`.

| Factor | Votes |
|---|---|
| chemical_induced_disease_relation::predicate_meaning | covered, covered, partial |
| causal_polarity::modifier | covered, covered, partial |
| chemical_to_disease_direction::modifier | covered, covered, partial |

## bc5cdr::train::18631865::perturb::argument_swap
Dataset: `bc5cdr`; variant: `argument_swap`.
Edge: `rapamycin --chemical_disease_interaction--> proteinuria`.

| Factor | Votes |
|---|---|
| chemical::subject_domain | covered, covered, absent |
| disease::object_domain | covered, covered, absent |
| chemical_induced_disease_relation::predicate_meaning | covered, covered, absent |
| causal_polarity::modifier | covered, covered, absent |
| document_level_evidence::modifier | covered, covered, absent |

## bc5cdr::train::18162529::perturb::polarity_flip
Dataset: `bc5cdr`; variant: `polarity_flip`.
Edge: `sulpiride --chemical_disease_interaction--> hyperprolactinemic`.

| Factor | Votes |
|---|---|
| chemical_induced_disease_relation::predicate_meaning | covered, covered, partial |
| causal_polarity::modifier | covered, covered, partial |
| document_level_evidence::modifier | covered, covered, absent |
| chemical_to_disease_direction::modifier | covered, covered, partial |

## bc5cdr::train::18503483::perturb::node_deletion
Dataset: `bc5cdr`; variant: `node_deletion`.
Edge: `tacrolimus --chemical_disease_interaction--> brachial neuritis`.

| Factor | Votes |
|---|---|
| disease::object_domain | absent, covered, partial |
| chemical_induced_disease_relation::predicate_meaning | absent, covered, partial |
| causal_polarity::modifier | absent, covered, partial |
| document_level_evidence::modifier | absent, covered, covered |
| chemical_to_disease_direction::modifier | absent, covered, partial |

## bc5cdr::train::6861444::perturb::node_deletion
Dataset: `bc5cdr`; variant: `node_deletion`.
Edge: `noradrenaline --chemical_disease_interaction--> hypertension`.

| Factor | Votes |
|---|---|
| chemical_induced_disease_relation::predicate_meaning | covered, covered, partial |
| causal_polarity::modifier | covered, covered, partial |
| document_level_evidence::modifier | covered, covered, absent |
| chemical_to_disease_direction::modifier | covered, covered, partial |

## drugprot::train::10901669::perturb::polarity_flip
Dataset: `drugprot`; variant: `polarity_flip`.
Edge: `TCDD --chemical_activates_gene_or_protein--> gamma-glutamyl carboxylase`.

| Factor | Votes |
|---|---|
| chemical_to_gene_or_protein_direction::modifier | absent, covered |
| direct_evidence::modifier | absent, partial |

## web_nlg_en-validation-814::perturb::argument_swap
Dataset: `webnlg`; variant: `argument_swap`.
Edge: `3Arena --owner--> Live Nation Entertainment`.

| Factor | Votes |
|---|---|
| entity_relation::predicate_meaning | covered, absent |

## bc5cdr::train::9100294::perturb::polarity_flip
Dataset: `bc5cdr`; variant: `polarity_flip`.
Edge: `verapamil --chemical_disease_interaction--> Cardiovascular alterations`.

| Factor | Votes |
|---|---|
| chemical_to_disease_direction::modifier | partial, covered |

## web_nlg_en-validation-858::perturb::relation_blur
Dataset: `webnlg`; variant: `relation_blur`.
Edge: `Anaheim, California --isPartOf--> Orange County, California`.

| Factor | Votes |
|---|---|
| part_whole_relation::predicate_meaning | absent, partial |

## drugprot::train::12751792::perturb::argument_swap
Dataset: `drugprot`; variant: `argument_swap`.
Edge: `N --part_of_relation--> mitochondrial and cytosolic forms of PHGPx`.

| Factor | Votes |
|---|---|
| chemical::subject_domain | covered, absent |
| part_whole_relation::predicate_meaning | covered, absent |
| chemical_to_gene_or_protein_direction::modifier | covered, absent |
| direct_evidence::modifier | covered, absent |

## bc5cdr::train::17600377::perturb::node_deletion
Dataset: `bc5cdr`; variant: `node_deletion`.
Edge: `scopolamine --chemical_disease_interaction--> cognitive deficits`.

| Factor | Votes |
|---|---|
| chemical_induced_disease_relation::predicate_meaning | covered, partial |
| causal_polarity::modifier | covered, partial |
| chemical_to_disease_direction::modifier | covered, partial |

## web_nlg_en-validation-1321::perturb::node_deletion
Dataset: `webnlg`; variant: `node_deletion`.
Edge: `Adonis Georgiadis --inOfficeWhilePrimeMinister--> Antonis Samaras`.

| Factor | Votes |
|---|---|
| entity_relation::predicate_meaning | partial, covered |

## drugprot::train::11153163::perturb::edge_deletion
Dataset: `drugprot`; variant: `edge_deletion`.
Edge: `indomethacin --chemical_inhibits_gene_or_protein--> COX-1`.

| Factor | Votes |
|---|---|
| inhibition_relation::predicate_meaning | covered, partial |
| negative_polarity::modifier | covered, partial |
| chemical_to_gene_or_protein_direction::modifier | covered, partial |

## bc5cdr::train::2024540::perturb::relation_blur
Dataset: `bc5cdr`; variant: `relation_blur`.
Edge: `angiotensin converting enzyme (ACE) inhibitors --chemical_disease_interaction--> hypotension`.

| Factor | Votes |
|---|---|
| chemical_induced_disease_relation::predicate_meaning | covered, partial |
| causal_polarity::modifier | covered, partial |
| chemical_to_disease_direction::modifier | covered, partial |

## bc5cdr::train::1468485::perturb::relation_blur
Dataset: `bc5cdr`; variant: `relation_blur`.
Edge: `cyclophosphamide --chemical_disease_interaction--> hematuria`.

| Factor | Votes |
|---|---|
| chemical_induced_disease_relation::predicate_meaning | covered, partial |
| causal_polarity::modifier | covered, partial |

## bc5cdr::train::1616457::perturb::relation_blur
Dataset: `bc5cdr`; variant: `relation_blur`.
Edge: `pentobarbital --chemical_disease_interaction--> amnesia`.

| Factor | Votes |
|---|---|
| chemical_induced_disease_relation::predicate_meaning | covered, partial |
| causal_polarity::modifier | covered, partial |

## web_nlg_en-validation-1657::perturb::node_deletion
Dataset: `webnlg`; variant: `node_deletion`.
Edge: `Hypermarcas --industry--> Pharmaceuticals`.

| Factor | Votes |
|---|---|
| entity_relation::predicate_meaning | covered, absent |
| entity::object_domain | covered, absent |

## bc5cdr::train::10365197::perturb::node_deletion
Dataset: `bc5cdr`; variant: `node_deletion`.
Edge: `Cocaine --chemical_disease_interaction--> mood disorder`.

| Factor | Votes |
|---|---|
| chemical::subject_domain | covered, partial |
| chemical_induced_disease_relation::predicate_meaning | covered, partial |
| causal_polarity::modifier | covered, partial |
| chemical_to_disease_direction::modifier | covered, partial |

## web_nlg_en-validation-1602::perturb::relation_blur
Dataset: `webnlg`; variant: `relation_blur`.
Edge: `Accademia di Architettura di Mendrisio --country--> Switzerland`.

| Factor | Votes |
|---|---|
| entity_relation::background | covered, absent |

## drugprot::train::11470741::perturb::edge_deletion
Dataset: `drugprot`; variant: `edge_deletion`.
Edge: `Cerivastatin --chemical_inhibits_gene_or_protein--> HMG-CoA reductase`.

| Factor | Votes |
|---|---|
| inhibition_relation::predicate_meaning | covered, partial |
| direct_evidence::modifier | covered, partial |
