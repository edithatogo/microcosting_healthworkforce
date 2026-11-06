# Candidate workbook profile unit audit — 6 November 2026

A read-only type audit of the retained 260-section candidate profile examined
17,175 cells with a declared unit. It found 136 literal text cells labelled with
numeric units: 120 formatted ALL component summaries, and 16 column labels in
four repeated publication-comparison headers. Formula cells were not treated as
literal text. This audit does not determine whether a formula returns a number.

The merged component mapping separates the 120 formatted summaries from numeric
jurisdiction values. In `Labour - Prices (DSA, Pub)`, rows 8, 15, 22 and 29
repeat comparison headers, alongside the already identified row 1 header. The
private successor profile replaces the component definitions with the merged
mapping and treats all five rows as headers in the comparison section. It has
262 sections, accounts for all 27,929 populated cells exactly once, retains
the empty `Labour - BY (%)` sheet, and has zero literal text cells carrying a
numeric unit under this check. It preserves the prior profile and workbook bytes.

The successor is retained as
`.private-runs/workbook-source-inventory/v3-table-profile-components.json`.
Zero findings in this type check do not establish that remaining units, table
boundaries, formulas or assumptions are semantically correct, nor that historical
values are accepted conditions. The checked-in component mapping is integrated;
the wider profile remains a candidate and needs further review and implementation.

## Publication comparison labels and formulas

The five comparison blocks begin at rows 2, 9, 16, 23 and 30 of
`Labour - Prices (DSA, Pub)`. Their column-BA role labels identify the
denominator blocks, and each block has six jurisdiction or ALL rows. A
read-only trace checked all 120 formulas in columns BD–BG: each divides an
explicitly referenced BC value by the BC value in its own row, and each
numerator has the same jurisdiction label as its denominator. No denominator
block is compared with itself.

The heading `BI` in `BD1` and `BS` in `BE15`, `BE22` and `BE29` both point,
through the formula references, to the `Bioinformatics staff` numerator block.
Preserve the original heading text and attach the formula-derived numerator
identity separately; the abbreviation alone does not establish author intent.
These ratios compare archived hourly midpoint values; they are not evidence of
an individual salary, workforce-weighted mean, statistical interval or
accepted industrial condition. The source workbook and formula bytes were not
changed.
