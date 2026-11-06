# Workforce v2 implementation and source screening — 6 November 2026

## Workbook extraction

The executable table segmenter has been run against workbook SHA-256
`c72a5f9d8a232ee559516978537a7efdd1aea6df55738e9d851840fff837ddca`.
The private candidate extract contains 152 sections and accounts for all 27,929
populated cells exactly once, with zero unassigned or overlapping cells. The
empty `Labour - BY (%)` sheet is recorded separately. Known splits include the
input and Year 0–4 blocks of the five workforce jurisdictions in both unweighted
and WM sheets, dollar/share component tables, weighting arrangements and
publication numeric/display blocks. Individual values retain sheet and cell
coordinates, formulas, cached-value state, original data types and formats.

This is not complete semantic incorporation: 68 physical regions still have
unresolved semantic subdivision, and the remaining sections are candidate
mappings requiring review. A private candidate register separately records 400
field-level values or formulas across the 25 workforce rows and 145 JSON leaf
values with source pointers and hashes. Units described as assumed, missing
sources, formulas without caches, historical estimates and model assumptions are
not promoted to verified entitlements. The split/mapping profile and exact
candidate extracts are retained under `.private-runs/workbook-source-inventory/`.

## Evidence and scoped gaps

The 576-target screening denominator remains eight jurisdictions by twelve broad
profession families by six sectors. It is a prioritisation matrix, not a census
of employers, grades, or required instruments. Discovery links were associated
with 118 target cells through 230 scoped keyword or national-award leads; these
are not counts of held or applicable instruments. Keyword navigation noise,
general titles and sector uncertainty remain. An empty match does not mean that
no relevant instrument exists. All targets remain applicability-unassessed.
See private `gap-screening-linked.csv` and `gap-discovery-leads.json` in
`.private-runs/workforce-source-coverage-20261106/`.

Six source PDFs were retrieved from the NSW Health official index, with source
URLs, retrieval times and byte hashes in `nsw-instrument-manifest.json`: the
administrative staff, general administrative staff, technical, hospital scientists,
health professionals, and public health nurses/midwives awards. Their presence
is distinct from verifying the historical workbook rows or any specific worker.
Both administrative awards exist as separate instruments, so the workbook's
blank NSW administration source cannot be resolved from a generic role label.
The general administrative instrument's clause 7 states a 1 July 2025 effective
start and salary schedules applying from the first full pay period on or after
1 July 2025 and 1 July 2026; employer, classification, pay-cycle date, prior
instruments and later variations must still be determined. The workbook's older
input year cannot be silently replaced by this edition. The Hospital Scientists
award clause 40 also makes several hours, roster, overtime, higher-duties and
annual-leave changes dependent on an employer notice; the implementation date
is not established by the PDF alone. This blocks automatic selection of those
conditions until the notice or other authoritative evidence is obtained. Source PDF layout was
visually inspected for that clause. The Queensland Industrial Relations Commission
also lists separate health-practitioner/dental, medical-officer and nursing
instruments; the exact worker and award/agreement chain still require review.

Earlier direct index requests for Queensland, Tasmania and NT returned HTTP 403.
The publicly accessible QIRC index is a useful alternate official discovery route,
but it does not establish coverage of the other inaccessible sources. Historical
editions, first-full-pay-period dates, classifications, contractual overrides,
redistribution terms and source review remain open. No real-world value has
been admitted to an accepted condition release.

Official discovery references: [NSW Health awards index](https://www.health.nsw.gov.au/careers/conditions/Pages/awards.aspx),
[NSW general administrative award](https://www.health.nsw.gov.au/careers/conditions/Awards/hsu-he-general-administrative-staff.pdf),
[Queensland Industrial Relations agreements](https://www.qirc.qld.gov.au/agreements/public-service-agreements),
and [Queensland health practitioners and dental officers award register](https://www.qirc.qld.gov.au/documents/3381).

## Versioned conditions and costing

The candidate source implementation provides scoped, date-bounded condition
releases and the deliberately limited `annual_salary_components_v1` method:
annual salary and fixed amounts per explicit annual paid hour, with percentage
components applied only to salary. A dated activity API splits at local calendar
day boundaries, calculates elapsed hours including DST, and reports the condition
identities used in each segment. This does not derive payroll cycles, legal
coverage, productive hours, overtime, leave, shift penalties or uncertainty.
The existing PSA inputs and legacy calculation remain untouched.

Synthetic regression tests exercise source scope and horizons, units, date
changes, source lineage, overlap rejection, equal-rate static/dynamic comparison
and elapsed DST hours. On Python 3.15.2 the repository `make ci` gate passed with
120 tests, strict type checking, Ruff and Bandit. A subsequent CLI change passed
`make ci` with 121 tests and an isolated installed-wheel synthetic CLI calculation
returned the expected total of 50 on Python 3.15.2. These checks do not qualify
real-world instruments, extracted economic meaning or archived workbook outputs.
