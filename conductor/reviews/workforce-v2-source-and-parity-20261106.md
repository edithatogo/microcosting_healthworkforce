# Workforce source and archive parity continuation — 6 November 2026

## Victorian medical-scientist source comparison

A 2021–2025 Medical Scientists, Pharmacists and Psychologists Victorian Public
Sector single-interest enterprise agreement was retrieved from the [Moyne Health
Services public source](https://moynehealth.vic.gov.au/wp-content/uploads/2023/07/2021-2025-Medical-Scientists-Pharmacists-and-Psychologists-Victorian-Public-Sector-Single-Interest-Employers-Enterprise-Agr.pdf).
The retained PDF SHA-256 is
`184c2235b2550194a316521ef919ef1415ea9dba6f3003d7dab3ed28127dfde0`.
The source has 256 PDF pages. Poppler reported font-resource errors on some
pages, so text extraction is not accepted indiscriminately; the schedule header
on PDF page 143 and medical-scientist table on PDF page 146 were separately
rendered and visually checked. The employer list and commencement statements
were extracted as candidate context and require full verification before use.

The workbook's Victorian medical scientist row identifies the grade span as
`MS1-4(RX4)-MS4-5(RZ7)` in `Labour - Prices!E5`. Its lower base salary formula
`V5` uses the weekly amount matching RX1, rather than RX4, in the agreement's
first-full-pay-period-on-or-after 1 December 2022 column. The upper formula `X5`
matches RZ7 in that column. This comparison identifies a concrete internal grade
conflict, not a correction of the workbook or proof that this edition was the
original source: the workbook's `G5` cites a 2017–2021 document. The workbook
has no employer identity or first-full-pay-period calendar for the row. Clause 3
and Schedule 1 restrict coverage; clause 4 distinguishes agreement operation
from wage schedule timing. Exact employer, intended grade, agreement chain, actual
pay period and eligibility remain unresolved. The original row remains unchanged
and is not admitted to an accepted release. Details and page captures are under
`.private-runs/workforce-source-coverage-20261106/`.

## Archived bound reconciliation

The previous review matched 300 publication/long-archive midpoint rows, with
295 differing lower and upper pairs. Further comparison with the separate
baseline hourly archive found that for each of six axes—annual leave, retention,
leave loading, private practice, professional development and sick leave—the
25 individual-jurisdiction publication lower and upper bounds match the baseline
bounds, while the five ALL aggregates differ. This pattern is consistent with
baseline bounds being retained in those publication rows; because the publication
cells are literals, it does not establish the original generation procedure or
prove that other sensitivity axes are correct. A row-coordinate comparison and
axis-specific baseline counts are preserved privately. Reconciliation remains
open and no archived bound is a new confidence interval.

## Exact arithmetic and verification

Source commit `dc3ff70` adds exact rational totals to the condition-activity
result, alongside the existing Decimal total and component outputs. Before this
change, separately costing three 20-minute activities at an hourly rate of 50
and adding their Decimal totals produced a tiny context-precision difference
from one 60-minute activity. The new numerator/denominator is derived from the
original Decimal conditions and elapsed microseconds and gives exactly equal
rational totals under that split. A separate test covers a nonterminating annual
salary/hour ratio. The existing Decimal fields remain unchanged, and overtime,
minimum-engagement and capacity outputs did not yet provide rational totals at
that checkpoint; see the later exact-costing continuation.

`make ci` passed on the selected Python 3.15.2 environment: 135 tests, formatting,
lint, strict type checking and Bandit. These checks do not validate source
applicability, author intent, scientific parameter choices or archived workbook
bounds. Both tracks remain in progress.
