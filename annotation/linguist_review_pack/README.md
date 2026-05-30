# Expert review form for predicate factors

This folder contains a small expert-review package for checking predicate-factor decompositions in LEMON-Factor.

## Files

- `expert_validation_form.xlsx` — the form to fill in Excel or LibreOffice Calc.
- `FIELD_GUIDE.md` — short explanation of every editable column.
- `RETURN_FORMAT.md` — what to return after review.

## What this is

LEMON-Factor decomposes graph predicates into semantic factors. For example, a predicate such as `birthPlace` can be represented through factors such as person-like subject, biographical relation, and place-like object.

The review checks whether these proposed factors are correct, sufficient, and not excessive. It does not evaluate the whole paper, the generated texts, or the metric scores.

## What to do

Open `expert_validation_form.xlsx` and go to the `Review` sheet.

For each row, read:

- `domain`
- `predicate`
- `example_triple`
- `example_text`
- `proposed_factors`

Then fill only the yellow columns:

- `verdict`
- `missing_factors`
- `wrong_or_extra_factors`
- `direction_or_role_ok`
- `polarity_ok`
- `suggested_fix`
- `comment`

Do not edit the input columns on the left. The workbook uses separated, widened columns and yellow highlighting for answer fields to make editing easier.

## Review scale

Use the dropdown values where available:

- `yes` — acceptable.
- `partly` — mostly acceptable, but needs correction.
- `no` — incorrect.
- `unclear` — cannot decide from the example.
- `not_applicable` — use for direction or polarity when that feature is not relevant.

## Time budget

The file contains 50 rows. It is designed for a realistic 2–3 day review. Partial completion is acceptable: leave unfinished rows empty.

## Output

Return the filled `expert_validation_form.xlsx` file. No separate report is required.
