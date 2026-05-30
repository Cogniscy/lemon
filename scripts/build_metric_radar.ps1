$ErrorActionPreference = "Stop"

python -m lemon_factor.analysis.metric_radar `
  --scoring reports/scoring_webnlg.json reports/scoring_drugprot.json reports/scoring_bc5cdr.json `
  --mine reports/mine1_like_lemon_pilot.json `
  --triple reports/triple_f1_baseline.json `
  --out reports/metric_radar_comparison.json `
  --tex-out paper/figures/figure_metric_radar.tex
