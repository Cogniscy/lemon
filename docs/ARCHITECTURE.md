# Architecture

```text
graph + text -> schema/graphtext -> coverage/ -> lexical factor coverage + trace
predicate inventory ----------------^

perturbed record + intended damage -> scoring/baselines -> factor damage proxy
predicate inventory --------------------------^

saved scoring reports -> report_schema -> aggregate/recompute -> tables and plots
```

The two scoring paths use different evidence. The proxy must not be described
as the lexical scorer's measured detection performance.

The installed CLI uses `importlib.resources` to read its own small demo dataset.
Research CLIs retain their module entry points and accept external paths.
Research inventories under repository `resources/` are not implicitly required
by installed-package examples.

Reports contain explicit schema versions. Readers migrate known legacy perturbation
formats in memory; original files remain untouched. See [formats](REPORT_FORMATS.md).
New recomputation defaults write to `artifacts/`.

LLM clients, datasets and dense models are optional research facilities.
They are not imported or invoked by the demo.
