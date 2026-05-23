# LEM-01 Build Results

Patch: LEM-01 Scope & Claims Freeze

## Tests

Command:

```bash
python -m pytest -q
```

Result:

```text
176 passed in 0.86s
```

## PDF build

Command:

```bash
cd paper
latexmk -pdf -interaction=nonstopmode main.tex
```

Result:

```text
Output written on main.pdf (14 pages, 364015 bytes).
Latexmk: All targets (main.pdf) are up-to-date
```

## PDF verification

Rendered all pages to PNG with the PDF skill renderer:

```bash
python /home/oai/skills/pdfs/scripts/render_pdf.py paper/main.pdf --out_dir render --dpi 120
```

Result:

```text
Rendered 14 page(s)
```

## Notes

The build still emits minor overfull/underfull hbox warnings. No build-stopping LaTeX errors were observed.
