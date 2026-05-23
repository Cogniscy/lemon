# lemon-01 / LEM-01 test results

## Scope

This report records the validation run after the LEM-01 scope and claims freeze patch.

## Commands

```bash
python -m pytest -q
cd paper && latexmk -pdf -interaction=nonstopmode main.tex
```

## Results

```text
176 passed in 1.11s
```

LaTeX build completed and produced `paper/main.pdf` with 14 pages. Remaining overfull/underfull hbox warnings are formatting issues, not build failures.
