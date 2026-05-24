# LEM-10.2 OpenRouter reliability runner stabilization

This patch fixes the local test regression introduced by excluding mock judgments from reliability summaries by default. The old mock-based unit test now checks both behaviors: default exclusion and explicit inclusion via `include_mock=True`.

It also adds short PowerShell wrapper scripts so long OpenRouter commands do not have to be typed into PSReadLine interactively. This avoids the Windows console rendering bug observed during the multi-line command entry.

## Added scripts

- `scripts/run_llm_balanced_pilot.ps1`: runs a balanced OpenRouter pilot over WebNLG, DrugProt, and BC5CDR.
- `scripts/summarize_llm_reliability.ps1`: summarizes real judgments while excluding mock judgments by default.

## Recommended command

```powershell
.\scripts\run_llm_balanced_pilot.ps1 -PerDataset 15 -Fresh
.\scripts\summarize_llm_reliability.ps1
```

The script uses `google/gemini-2.0-flash-001`, `json_schema`, fallback `json_object`, response healing, and progress reporting. It writes one combined judgment file plus per-dataset reports.
