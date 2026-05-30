# LEM-16A implementation report

Added:

- `src/lemon_factor/baselines/mine1_like/core.py`
- `src/lemon_factor/baselines/mine1_like/prepare.py`
- `src/lemon_factor/baselines/mine1_like/score.py`
- `src/lemon_factor/baselines/mine1_like/validate_mine_formula.py`
- `src/lemon_factor/baselines/triple_f1.py`
- `scripts/run_mine1_like_pilot.ps1`
- `scripts/run_mine_external_smoke.ps1`
- `tests/test_mine1_like.py`

The local score follows the MINE-1 aggregation formula: mean of binary fact-recoverability decisions. In LEM-16A, the binary decision is deterministic and lexical so that tests and smoke runs are reproducible without API calls. This should be described as MINE-1-compatible or MINE-inspired until a public KGGen/MINE subset is run externally.
