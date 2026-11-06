# Workbook component summary lineage — 6 November 2026

The original workbook `Sum Cost Comp!A2:M7` contains a five-occupation numeric
summary plus formatted salary-range strings. `A9:F21` transposes the same
fields and occupations. A read-only check of the workbook with SHA-256
`c72a5f9d8a232ee559516978537a7efdd1aea6df55738e9d851840fff837ddca`
matched all 55 numeric summary values to their transposed copies and to the
arithmetic mean of the five corresponding jurisdiction input cells on `Labour -
Prices`. The check also verified the associated 55 `ALL` average formulas and
five pairs of salary display strings. One source input, `Labour - Prices!S32`,
is the formula `=160/40`; the check evaluates that specific expression as four
rather than treating it as a literal or an absent cached value.

The summary omits productive-time fraction from the source columns. It keeps
fractions, hours per week, annual development allowance, weeks of leave and
annual indexation distinct; the salary range remains formatted text rather than
a numeric interval. Because the summary cells are literals, numerical agreement
with the means does not prove their generation history, authority or suitability
as conditions for an individual worker. The resulting values are historical
candidates, not reviewed entitlements or workforce-weighted estimates.

A private versioned candidate extraction splits the transposed section by field,
assigns candidate units and retains source-cell lineage. The independent
private verification script and `component-summary-lineage.json` preserve the
55 field-level comparisons; the source workbook hash was unchanged. The new
profile has 260 candidate sections, accounts for 27,929 populated cells with no
unassigned cells, and retains the empty sheet. These counts demonstrate raw
assignment, not semantic acceptance of every other section. The existing
248-section profile was preserved.
