# lemon-02.1 test results

Command:

```bash
python -m pytest -q
```

Result:

```text
29 passed
```

Notes:

- Added offline tests for deterministic stratified sampling.
- Added dataset-statistics tests for category ratios and edge-count distribution.
- Existing WebNLG converter tests still pass.
