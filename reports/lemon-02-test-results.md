# lemon-02 test results

Command:

```bash
python -m pytest -q
```

Result:

```text
20 passed
```

Scope added in lemon-02:

- WebNLG triple parsing and label normalization.
- WebNLG record to GraphText conversion.
- Validation split mapping to `dev`.
- Dataset statistics on converted examples.
- Existing GraphText, factor metric, MINE retrieval, and unified JSONL tests remain green.
