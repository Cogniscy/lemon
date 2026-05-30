# LEM-23: Linguist Excel review pack

## Goal

Make the expert-validation sample easier to review by replacing CSV editing with a structured Excel workbook and collecting all reviewer-facing instructions in one folder.

## Created folder

`annotation/linguist_review_pack/`

## Files

- `annotation/linguist_review_pack/expert_validation_form.xlsx`
- `annotation/linguist_review_pack/README.md`
- `annotation/linguist_review_pack/FIELD_GUIDE.md`
- `annotation/linguist_review_pack/RETURN_FORMAT.md`

## Workbook structure

- `Review` — 50 predicate-factor rows. Input columns are on the left; editable reviewer columns are highlighted in yellow.
- `Instructions` — short task description.
- `Legend` — allowed values and examples.
- `Summary` — simple progress and rate formulas.

## Reviewer workload

The workbook uses the same 50-row sample as `annotation/expert_validation_sample.csv`:

- 36 WebNLG rows
- 12 DrugProt rows
- 2 BC5CDR rows

This remains a 2--3 day expert-review package, not a full validation of the entire factor inventory.

## Safe claim

A compact expert-review package has been prepared for predicate-factor validation.

## Unsafe claim

The full inventory is already expert-validated.
