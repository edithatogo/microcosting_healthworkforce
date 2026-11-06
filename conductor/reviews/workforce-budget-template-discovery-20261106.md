# Workforce budget template discovery — 6 November 2026

The NSW Health Budget Buildup Tool and Queensland Health labour budgeting
workbooks are additional comparison sources, not authority to publish their
contents or to apply their historical inputs as current entitlements. Their
restricted copies and native locations are retained in private evidence. The
workbooks may contain populated operational data; do not add them or extracted
rows to this public repository.

The NSW workbook was read from the private source repository at a pinned
revision. Its 23 sheets include award, pay-calendar, position, time and
financial reference structures. The source repository's first-pass inventory
reports 11,022 formula cells, 855 exported named ranges and 99 first-pass
formula rules. These are discovery figures, not an independently verified
calculation or VBA parity claim.

A read-only Queensland Health SharePoint search located a 2018 costing workbook
and two later populated examples of a labour/FTE costing template. The later
examples have separate calculation sheets for salary, pay-point progression,
leave backfill and loading, several allowance families, overtime, penalties,
superannuation, long-service leave levy and workers compensation. The older
workbook includes multiple professional streams and non-labour costs. A 2026
modified date on an attachment establishes neither current rates nor general
approval. Do not execute workbook macros.

## Implications for both tracks

- Add these workbooks to private source discovery as contextual budgeting
  comparisons, with their version and provenance kept distinct from primary
  awards, agreements and reviewed conditions.
- Compare calculation categories, time boundaries, pay progression, FTE and
  headcount, leave backfill and on-cost bases with the versioned costing model.
  Map individual rules and dependencies only after inspecting their formulas
  and authoritative instruments; do not equate sheet names with implemented
  or validated behaviour.
- Retain the existing source-applicability and scientific validation gaps.
  Templates may include local conventions, forecasts, assumptions and filled-in
  values; they do not establish cross-jurisdictional or individual eligibility.
- Before reuse or redistribution, resolve source rights, sensitivity, date,
  scope and ownership. Any runnable parity fixture must use synthetic inputs
  and must not expose private workbook content.

Structural inspection used the repo-local Python 3.15.2 and read-only workbook
loading. It did not evaluate formulas, run macros, test calculated parity, or
verify the current Queensland template against its owner.
