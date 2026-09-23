# Offline example

Run `python -m lemon_factor demo` after installation, from any directory.
The single source of fixture data is
`src/lemon_factor/demo_data/cases.json`, included in the wheel.

Four synthetic texts cover a supported fact, a missing relation cue, negation and
a relation belonging to another participant. The last two deliberately expose
known limitations; high scores there are not correct semantic judgments.

Use `python -m lemon_factor reproduce-demo --out artifacts/demo` for scores,
a Markdown summary and a manifest. No external data or API key is required.
