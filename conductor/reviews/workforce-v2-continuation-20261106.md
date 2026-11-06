# Workforce v2 continuation — 6 November 2026

## Workbook mappings

The private candidate profile now segments the 20-sheet workbook into 240
sections. It assigns all 27,929 populated cells exactly once; the empty sheet is
recorded separately. The profile splits the DSA input/baseline and ten
sensitivity axes, archived wide DSA results, monetary and fractional component
blocks, formatted displays, five years of nominal and WM outputs, and weighted
aggregate midpoint/bounds. It retains formulas and original coordinates and does
not evaluate missing formula caches.

A focused reconciliation checked `Components $ and %!C3` as a candidate AUD
amount and `C35` as a fraction, `Labour - Prices (Fixed header)!O2` as percent
per year, and the WM `Z46` weighted midpoint versus `Y46` minimum-bound role.
`Labour - Prices (DSA)!AK39` is an isolated literal zero with unknown role and
is explicitly retained as unresolved; zero is not interpreted as missing. The
240-section profile contains candidate and archive mappings, not 240 approved
semantic tables. Some broad display, DSA aggregate, assumptions and component
sections still require finer review, column meaning/units and reconciliation to
legacy outputs. The private profile and extract are in
`.private-runs/workbook-source-inventory/`; source workbook hash is unchanged.
No original-model formula recalculation or complete semantic parity is claimed.

## Source and applicability progress

The Queensland Industrial Relations Commission's 2022 Health Practitioners and
Dental Officers agreement was retrieved as a distinct edition and SHA-256 checked;
its acquisition metadata and extracted candidate records are private. Clause 6.2
and its table were visually checked on PDF page 31 (printed page 29). The table
has separate categories and dated amounts; the table's period unit and category
assignments are not yet established from the checked page. Clause 6.2.2 excludes
the allowance from leave loading, penalty-rate, overtime and superannuation
calculations. Clauses 6.2.3–6.2.4 specify distinct permanent part-time and
temporary eligibility; development leave has a different temporary-service
threshold. The employer, classification, individual employment basis, policy C42,
operative date and subsequent variations must be established before any amount or
rule is admitted to an accepted release. No individual workbook role was thereby
verified, and the existing 2019 GHA evidence is not replaced.

Official references: [Queensland agreement and historic editions](https://www.qirc.qld.gov.au/documents/3656),
[2022 agreement text](https://www.qirc.qld.gov.au/sites/default/files/2023-06/2023_cb43.pdf),
and the [NSW Industrial Relations Commission historical hospital scientists index](https://sheriff.nsw.gov.au/content/dcj/ctsd/irc/irc/industrial-instruments/awards/current-awards/590---hospital-scientists-state-award.html).
The NSW official gazette index also lists separate 2022 administrative and
general-administrative awards (C9522 and C9542). Their presence narrows the
discovery gap but does not resolve the workbook's missing employer/classification
information or establish an accepted row. The NSW index identifies a 2022
hospital-scientists edition relevant to discovery, but a direct
attempt to retain its Industrial Gazette PDF timed out; it is not held or linked
to a verified individual workbook row. Queensland's original wage/index routes,
Tasmanian and NT source routes previously returned HTTP 403. Alternative official
routes can continue to be assessed without treating access to one page as proof
of access to all instruments. The nationwide 576-cell matrix remains unassessed
for specific employers and grades; no accepted national coverage count is claimed.

## Costing and validation

Source commit `30da372` adds `cumulative_salary_overtime_v1`: one explicitly
reviewed salary-only multiplier, a caller-supplied pay period and cumulative
prior hours, a complete-history assertion, ordered nonoverlapping activities and
source/date checks. It preserves condition and rule provenance. It does not
infer eligibility, pay-period starts, all eligible time, multiple overtime tiers,
minimum engagements, penalty stacking or rounding. A single threshold is not a
representation of all actual awards. The history assertion is supplied by the
caller, not independently verified by the library.

Synthetic tests cover an independently calculated threshold crossing, missing
history, overlapping activity, source hash mismatch, pay-period crossing and
adjacent-segment equivalence. Full `make ci` passed on repo-local Python 3.15.2:
125 tests, Ruff formatting/lint, strict type checks and Bandit. Subsequent source
commit `f9fdb44` adds an explicit productive-capacity scenario: paid base cost
remains intact, disjoint lost hours and incremental cover are caller assumptions,
and the denominator describes the original worker only. Full `make ci` then
passed 127 tests with the same checks. No accepted real-world rule bundle or full
source-backed roster validation has been produced.
The existing legacy and PSA model behaviour remains unchanged.
