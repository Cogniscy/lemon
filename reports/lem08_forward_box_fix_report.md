# LEM-08 Forward box figure fix

## Change

Adjusted the TikZ Figure 1 layout so that connector arrows no longer overlap the text inside the Forward LEMON and Reverse LEMON boxes.

## Files changed

- `paper/figures/figure_predicate_factor_evaluation.tex`
- `paper/main.pdf`
- `paper/build/lemon_lem08_forward_box_fix.pdf`

## Verification

- LaTeX build: passed.
- PDF length: 15 pages.
- Render check: 15 pages rendered.
- Page 5 inspected after rendering; Forward LEMON text is unobstructed.

## Notes

No Python source files were changed in this patch.
