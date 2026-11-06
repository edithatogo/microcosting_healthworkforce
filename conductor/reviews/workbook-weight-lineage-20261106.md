# Workbook Medicare weight lineage — 6 November 2026

A coordinate-level check of the retained original workbook (SHA-256
`c72a5f9d8a232ee559516978537a7efdd1aea6df55738e9d851840fff837ddca`)
traced the eligible-person counts in `Medicare Enrolments!B19:I19` to the
literal copies in `Weightings!A2:B9`. All eight jurisdiction/value pairs match.
`Weightings!F2:G6` repeats the five selected jurisdictions in the order VIC, SA,
NSW, QLD, WA, and its literals agree with those source counts. `H2:H6` divides
those counts by their five-state sum.

For each of the five occupational rows, `Labour - Prices (WM)!Z46:Z50` and
`AC46:AC50` combine the corresponding salary and hourly midpoint cells using
those five weights in the same jurisdiction and occupation order. The private
`verify-weight-lineage.py` checks all ten formulas, all eight copies and all
five weight formulas and verifies that workbook bytes remain unchanged.

This traces a historical calculation and its selected denominator; it does not
establish that Medicare enrolments are a defensible proxy for workforce or
activity distribution. Three jurisdictions are outside that weighted aggregate.
The check does not recalculate cached workbook results, validate the lower and
upper bounds as statistical intervals, or accept any source-specific condition.
Other semantic sections and applicability questions remain open.
