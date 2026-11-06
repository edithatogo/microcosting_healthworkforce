# Workforce v2 mapping review and tiered overtime — 6 November 2026

## Workbook mapping review

The private workbook profile now has 248 candidate sections with all 27,929
populated cells assigned once and the empty sheet retained. It further separates
Medicare card counts, eligible-person counts, ratios, method notes and historical
system-change values. It also separates publication numeric, formula/display and
comparison sections and records the Medicare denominators and fractions as
historical enrolment weights, not workforce or activity weights. Candidate units
and identities remain subject to review; section counts do not establish complete
semantic acceptance.

A direct comparison matched 240 publication sensitivity rows to the long archive
by exact role, jurisdiction and axis label and a further 60 after the explicitly
recorded label aliases `Hours worked`/`Hours worked per week` and
`Superannuation`/`Superannuation Rate`. These are label matches, not proof that
the underlying sensitivity axes have equivalent definitions. All 300 midpoint
pairs matched at relative and absolute tolerance 1e-12; 295 lower-bound pairs
and 295 upper-bound pairs differed. Five pairs of each bound matched. Both
historical tables remain separate, and neither set of bounds is reclassified as
a validated uncertainty interval. Full private row-coordinate results and the
comparison script are in `.private-runs/workbook-source-inventory/`.

`Labour - Prices (DSA)!AK39` is a literal numeric zero. A scan of parsed direct
and rectangular formula references found none referring to it; no `INDIRECT` or
`OFFSET` formulas were found and no range operands in the relevant scan were
unparsed. This narrows its observed role but does not establish why the cell was
created. Preserve it as an unresolved historical literal, not a missing value.

## Source acquisition and applicability

An official NT index discovery identifies separate NTPS nursing/midwifery,
Aboriginal health practitioner and general employee agreement leads. Tasmania's
historical Department of Health reporting identifies allied health, ambulance
and nursing agreement leads. These are discovery records, not holdings or
assessed eligibility. Exact editions, employer/classification scope, variations
and operability still need their own primary instrument evidence. The attempted
alternative NT Health nursing page and Tasmanian Department of Health annual
report both returned HTTP 403; prior Queensland, Tasmania and NT direct access
failures also remain. The private `tas-nt-additional-discovery.json` and
`tas-nt-discovery-manifest.json` distinguish indexed leads from failed holdings.
No verified coverage is inferred from an index or a ballot.

Discovery references: [NT current-agreement index](https://ocpe.nt.gov.au/employment-terms-and-conditions/current-enterprise-agreements/enterprise-agreements-current),
[NT nursing agreement negotiation page](https://ocpe.nt.gov.au/employment-terms-and-conditions/current-enterprise-agreements/enterprise-agreement-negotiations/ntps-nurses-and-midwives-enterprise-agreement),
[Tasmanian Department of Health annual report 2023–24](https://www.health.tas.gov.au/sites/default/files/2024-10/department_of_health_annual_report_2023-2024.pdf),
and [Tasmanian workforce implementation report](https://www.health.tas.gov.au/sites/default/files/2024-07/health_workforce_2040_implementation_report.pdf).
Historical references are not evidence of current terms. Employer- and
classification-specific applicability remains unresolved throughout the matrix.

## Costing and checks

Source commit `872ef9b` adds nondecreasing cumulative salary-overtime tiers. It
requires explicitly supplied reviewed thresholds, source, dates, pay-period and
complete history, and counts base cost once while reporting incremental premiums.
Each higher-tier hour is also counted in earlier cumulative-threshold totals.
The method does not support decreasing rates, shift-specific triggers, minimum
engagements, interaction with penalties or inferred eligibility. No specific
award rule has been admitted to an accepted release on the basis of this code.

Synthetic tests include a hand-calculated two-tier example and rejection of
duplicate/decreasing tiers and unreviewed rules. Source commit `300b8b7` adds
a separate single-day minimum-engagement method: the caller confirms eligibility
and specifies which components apply to the guaranteed extra hours. It does not
combine that rule with overtime, penalties or cross-day changes. A subsequent
`make ci` passed on repo-local Python 3.15.2 with 133 tests, Ruff, strict type
checking and Bandit. Both tracks remain in progress; this is not national
source, economic or legal qualification.
