# LEM-03 Report: Factor Inventories

Status: passed.

LEM-03 adds fixed predicate-factor inventories for WebNLG, DrugProt, and BC5CDR. The validator confirms that weights sum to one and that the inventories cover the predicates in the current evaluation data.

| Dataset | Factors | Predicates | Data predicates | Coverage |
|---|---:|---:|---:|---:|
| WebNLG | 24 | 121 | 119 | 1.000 |
| DrugProt | 25 | 13 | 12 | 1.000 |
| BC5CDR | 25 | 1 | 1 | 1.000 |

The resources are scoped. WebNLG covers the current development split, DrugProt covers the normalized chemical-gene/protein predicates emitted by the converter, and BC5CDR covers the document-level chemical-induced disease relation.
