# lemon-02 — WebNLG parquet ingestion and unified GraphText conversion

## Goal

Build the first reproducible dataset layer for LEMON-Factor: load WebNLG through
its Hugging Face parquet conversion, convert train/dev examples to the unified
`GraphTextExample` schema, compute dataset statistics, and document the workflow
for the SPECOM paper.

This milestone deliberately does not evaluate extraction. WebNLG already has
explicit graph input: DBpedia-style triples paired with short texts. This lets the
project test graph-text meaning preservation on gold graphs.

## Why parquet loading is required

`load_dataset("GEM/web_nlg")` fails with recent `datasets` versions because
legacy dataset scripts are no longer supported by the default loader. The working
route is to load the converted parquet files directly:

```powershell
python -c "from datasets import load_dataset; ds=load_dataset('parquet', data_files={'train':'hf://datasets/GEM/web_nlg@refs/convert/parquet/en/train/*.parquet','validation':'hf://datasets/GEM/web_nlg@refs/convert/parquet/en/validation/*.parquet'}); print(ds); print(ds['train'][0])"
```

Observed fields:

```text
gem_id, gem_parent_id, input, target, references, category, webnlg_id
```

The `input` field is a list of triples such as:

```text
Aarhus_Airport | cityServed | "Aarhus, Denmark"
```

## Tasks

1. Add a WebNLG parquet loader.
2. Add robust triple parsing for pipe, parenthesized, and colon-separated forms.
3. Convert each WebNLG record to `GraphTextExample`:
   - subjects/objects become nodes;
   - triple predicates become edges;
   - each triple becomes a gold fact;
   - `target` becomes the primary text;
   - `category`, `webnlg_id`, `references` are preserved in metadata.
4. Write train/dev unified JSONL files.
5. Compute dataset statistics.
6. Add offline unit tests using synthetic WebNLG-like records.
7. Update README and roadmap.

## Commands

Install research dependencies:

```powershell
python -m pip install -e ".[dev,research]"
```

Inspect WebNLG fields:

```powershell
python scripts/inspect_webnlg.py
```

Convert a pilot subset:

```powershell
python -m lemon_factor.datasets.convert_webnlg --language en --n-train 100 --n-dev 50 --out-dir data/processed
```

Compute statistics:

```powershell
python -m lemon_factor.analysis.dataset_stats data/processed/webnlg_train.jsonl data/processed/webnlg_dev.jsonl --out data/reports/webnlg_stats.json
```

Run tests:

```powershell
python -m pytest
```

## Code artifacts

- `src/lemon_factor/datasets/normalization.py`
- `src/lemon_factor/datasets/webnlg_loader.py`
- `src/lemon_factor/datasets/convert_webnlg.py`
- `src/lemon_factor/analysis/dataset_stats.py`
- `scripts/inspect_webnlg.py`
- `tests/test_webnlg_converter.py`

## Paper artifacts

- First reproducible row for the Dataset Statistics table.
- Dataset conversion protocol for the Data section.
- Reproducibility note explaining why WebNLG is loaded through parquet.
- A clean example of using gold graph data rather than extraction output.

## Risks and mitigation

| Risk | Mitigation |
|---|---|
| `datasets>=4` cannot load `GEM/web_nlg` script | Use `load_dataset("parquet", data_files=...)` over `refs/convert/parquet`. |
| WebNLG split names differ | Loader supports train/validation/dev aliases. |
| Triple surface formats vary | `parse_webnlg_triple` supports pipe, parenthesized, and colon-separated forms. |
| Windows symlink warning from Hugging Face cache | Safe to ignore; optionally enable Developer Mode or set `HF_HUB_DISABLE_SYMLINKS_WARNING=1`. |
| Tests accidentally require network | Unit tests use synthetic fixtures only. Network inspection is manual. |
| Node duplication across triples | Nodes are deduplicated with deterministic stable IDs. |

## Acceptance criteria

- `python -m pytest` passes.
- `webnlg_train.jsonl` and `webnlg_dev.jsonl` are produced from parquet data.
- Every exported row validates as `GraphTextExample`.
- Dataset statistics are saved as JSON.
- README contains the WebNLG conversion commands.
