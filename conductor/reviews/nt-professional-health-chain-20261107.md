# NT professional-health source chain and holding reconciliation

This batch links three previously unheld public-sector target cohorts to actual
held NTPS/employer evidence: NT Health allied-health professionals, pharmacists/
pharmacy technicians and NT Health-employed paramedics. The scopes are partial;
they do not cover every employer or establish an actual worker's entitlement.
In particular the paramedic link does not establish St John/private ambulance
coverage. All 576 screening statuses remain `applicability_unassessed`.

## Actual holdings and source authority

The live official NTPS 2025–2029 agreement PDF is byte-identical to the existing
262-page holding, SHA-256
`893ac4e32e5078581d40dca32bfa438efcedf2ebfb943c3e9f4fa24ec55616ec`.
No duplicate agreement PDF was stored. The [official current-agreements index](https://ocpe.nt.gov.au/employment-terms-and-conditions/current-enterprise-agreements/enterprise-agreements-current)
continues to list the instrument. That index is web-readable; the exact raw index
request returned 403 and no local HTML holding is claimed for it. This does not
invalidate the successful exact PDF acquisition or require an authentication change.

Six new PDFs/16 pages and the official allied-health vacancy HTML are held with
hashes and acquisition receipts. Three PDFs are employer summaries, and three
are determinations: amended 1020/2026 pharmacy market/retention allowances,
re-issued 1/2026 annual allowances and 1006/2026 grandfathered P1/P2 allowance.
Eight typed source records, including the existing agreement, validate and
round-trip. Employer summaries and job advertisements provide supporting scope
leads; their benefits, salary bands and references are not governing rates.
The three determinations are listed on the [official determinations register](https://ocpe.nt.gov.au/employment-terms-and-conditions/determinations).

## Re-extracted conditions and timing

Eighteen candidate records distinguish market fractions, part-time quantities,
paid absence/compensation, casual status, premium bases, retention location,
service and assessment window, receipt-based exclusion, operative/transition/end
dates, approval undertakings, schedule gates and grandfathered classifications.
None becomes an actual-worker accepted or automatically enabled rule.

The [amended pharmacy determination](https://ocpe.nt.gov.au/__data/assets/pdf_file/0007/1613437/amendment-of-determination-1020-of-2026-market-and-retention-allowances.pdf)
states 15% market allowance for qualifying professional-stream pharmacists and
10% for qualifying technical-stream pharmacy technicians. Market payment is
fortnightly, pro-rata for part-time ordinary hours, continues during authorised
paid leave and workers' compensation, and does not count in overtime or other
penalty/allowance calculations. Market clauses expressly exclude the cited
casual category. Retention has separate eligibility and service rules; the
summary's casual-retention exclusion needs reconciliation with the full source.

Pharmacist retention distinguishes Darwin/Palmerston from locations outside them.
The assessment date is 6 February each year, with payment following that date,
not the individual's hire anniversary. Part-time and shorter-service proportions
are separate. Compensation periods and specified unpaid leave do not count as
retention service even though market allowance can continue during compensation.
Whether the unpaid-leave threshold excludes the whole absence or only its excess,
actual workday denominators, changing location/FTE and continuous service remain
unresolved. No fixed 365-day divisor or generic hourly accrual is imposed.

The pharmacy retention exclusion of EA clause 53 is triggered by receipt of that
allowance. The generic directed eligible-facts method cannot silently infer receipt
from bare eligibility. Future composition needs a separately established receipt
predicate, compatible units and a reviewed temporal relationship.

The handwritten amendment date was visually read as 13 May 2026. Raw OCR's
incorrect date and first-clause number are retained unchanged alongside images.
The determination operates from signature, separately providing a comparison with
hypothetical entitlement from 6 February 2026 for the transition period. Actual
amounts already received are required for any cash difference. Its endpoint is
the later of EA nominal expiry or replacement commencement, so 10 August 2029 is
not an automatic stop date while replacement commencement is unknown.

The approval decision dates the EA to 30 January 2026, operative 6 February 2026,
with nominal expiry 10 August 2029. Actual scanned undertakings were visually
reviewed: casual paid long-service leave; full-pay compassionate leave during
half-pay recreation leave with recreation-leave recredit; and the MA000151
clause 24A delegate minimum where more beneficial. These qualify the agreement
text. MA000151 and the original pre-amendment 1020 are referenced-only in this
batch. Schedule 3 still requires Department of Health employment, relevant
classification and union eligibility; a generic professional title is insufficient.

The incentives guide mixes EA editions and salary bands and points sonographer
conditions to 8.11 while the held EA has 8.10. Source reconciliation remains
explicit rather than adopting the summary wholesale. The re-issued annual
allowance determination and every grandfathered rate are held candidates, not
fully reviewed current rate quotes.

## Conditional static/dynamic composition

The installed unchanged calculator on Python 3.15.2 reproduces both market
fractions with salary-only premium bases. Synthetic salary is 100/hour, rising to
110/hour at midnight, with a hypothetical 50% premium. Pharmacist snapshot/dynamic
totals are exactly 165/346.50; technician totals are 160/336. Market is retained as
an additive salary fraction and excluded from the premium's named bases.
Salary amounts, annual paid-hours denominator, eligibility and premium entitlement
are analyst assumptions, not observed pay. No superannuation, retention cash,
transition payment, source parser or automatic policy guard is claimed.
Installed module bytes equal accepted main `4bd1b2e`; the prior 657-test and
main CI/Security receipts are reused, with no new full suite or native workbook run.

## Registration, correction and remaining work

Matrix v31 changes four rows. Three new NT public targets gain held-candidate
links and limited scope/next actions. The NSW operational-support row had held
candidate IDs but a stale no-held-instrument flag; its holding field is corrected
against verified held source bytes. This is an accounting correction, not an
applicability promotion. There are now 42/576 rows with candidate source IDs and
42 holding-status flags, resolving the prior 39-versus-38 discrepancy. Fully
accepted broad coverage remains zero; these counts measure holdings only.

Index v8 preserves all five price subsets and prior rule qualifications/capability
entries, adding the source batch separately. All price fields and all screening
statuses are unchanged. No new accepted price subset is claimed.

Private packet: `nt-professional-health-chain_20261107_v1` under the existing
source-coverage evidence directory. Raw sources and population/identity-bearing
material remain private; redistribution rights are unassessed.

- Source manifest v2: `9f00a02b955734400094773d204d62a0e1cddd4e02081a3d76a19bd35456f2bb` (initial manifest retained).
- Matrix v31: `1f2a4a6d1902f8f9cf71d3df44ee1ebdde51ba822d3a9ad02d843fe55187289a`.
- Index v8: `31f882ed81bbed451b1b7d963d9d976bb0f66f53a31ceb611c428132f5ce563a`.
- Terminal manifest: `d2fffb6f61d0cb9c5bddf77e3d3c3421e6aaede307a342b2358547aba089220b`.

Next: resolve original/determination and national-award dependencies, full salary/
allowance tables and actual cohort/schedule, service/FTE/absence histories, receipt
versus eligibility and retrospective entitlement versus cash. These are source
and implementation tasks; this batch does not establish a whole-track blocker.
Workbook unknowns and scientific PSA evidence remain separate open requirements.
Both tracks remain active.

## Delegate training comparator

The retained General EA clause 23.2 allows up to five paid training days
per annum for qualifying delegates and nominated representatives. Its
pay basis excludes shift penalties and overtime. The approval undertaking
requires a separate comparison with [MA000151 clause 24A](https://awards.fairwork.gov.au/MA000151.html)
where the award provision is more favourable. Clause 24A.8 uses the pay
the delegate would have received for the rostered or required hours and
has separate initial training, subsequent training, cohort and notice
conditions. The official consolidation through 1 July 2026 records the
retrospective substitution of clause 24A by PR795803.

For one dated training event, review the two eligibility routes separately.
Then compare complete pay alternatives for the same exposure. The quote
bundle engine can retain the ordinary-pay and rostered-pay components and
select one complete priced alternative. Eligibility, event approval,
roster, historical award edition and the undertaking's application to the
case must be established before pricing. The existing synthetic quote
bundle and paid leave checks qualify the arithmetic only.
