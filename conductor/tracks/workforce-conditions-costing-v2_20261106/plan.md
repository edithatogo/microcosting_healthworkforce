# Versioned extraction and static/dynamic costing — implementation plan

Status: in progress. Raw workbook intake, scoped source contracts and a limited
flat-hourly costing foundation are implemented; semantic extraction, source-backed
conditions and the remaining phases are not complete. See the receipt below.

The [minimum/overtime interaction review](../../reviews/minimum-overtime-interaction-20261106.md)
documents the double-counting hazard and the isolated implementation of one
explicitly selected interaction. Source commits `232edfe` and `6752a03` require
separate reviewed interaction evidence and preserve all rule provenance. Local
validation passed 152 tests, Ruff, strict basedpyright and Bandit on Python
3.15.2 using the existing qualified dependencies. A source distribution and wheel built; the wheel imported outside the checkout.
Outgoing-history Gitleaks and Presidio were reviewed; [PR #49](https://github.com/edithatogo/microcosting_healthworkforce/pull/49) passed exact-head checks and merged as `009dad2`. Receiving-main CI and Security passed; the merged source lane was retired. The synthetic scenario does
not establish an applicable real-world entitlement or complete other rule
interactions.

The [Victorian scientist reconciliation](../../reviews/victorian-scientist-source-reconciliation-20261106.md)
now traces the historical salary endpoints to the cited agreement's salary
circular and confirms the internal RX1/RX4 label conflict. The row remains an
unaccepted candidate pending grade intent and employer applicability.











## Tasmanian public-sector discovery — 6 November 2026

The [Tasmanian discovery review](../../reviews/tas-public-source-discovery-20261106.md) identifies later allied-health, ambulance, nursing and rural-medical leads and a documented distinction between ambulance decision and commencement dates. Direct decision downloads returned HTTP 403; source bytes, scope, variations and actual worker applicability remain unverified.

## Reviewed retrospective pay-period authority — 6 November 2026

[PR #62](https://github.com/edithatogo/microcosting_healthworkforce/pull/62), commit `bf5ba84`, adds an explicit reviewed retrospective interval and knowledge cutoff to first-full-period resolution. Synthetic tests preserve rejection without authority and check date bounds, source hash and employer scope. Local CI passed 178 tests, Ruff, strict basedpyright and Bandit on Python 3.15.2; outgoing Gitleaks and reviewed Presidio passed. PR #62 passed exact-head checks and merged as `4281e48`; receiving-main CI and Security passed. The clean worktree and local branch were retired; the remote branch was already absent. This does not infer retrospective legal effect or implement retrospective condition-release pricing, backpay or cash timing.

## Retrospective source boundary — 6 November 2026

The [source-boundary review](../../reviews/retrospective-source-boundary-20261106.md) records an ACT pay trigger predating the agreement's operation and a synthetic fail-closed reproduction. The current pay-period and source contracts cannot yet represent a verified later source as retrospective authority for an earlier entitlement date. Keep source operation, reviewed retrospective scope, knowledge date and cash timing distinct; do not change an operative date to force acceptance.

The isolated `codex/workforce-retrospective-conditions` worktree combines the
unmerged release-history source with commits `c17e8b5` and `6774222`: explicit
reviewed retrospective source coverage and a history guard against selection or
replay before the release's knowledge date. Synthetic static/dynamic and forged
early-replay checks pass. The combined local tree passed 185 tests, full Ruff,
basedpyright and Bandit on Python 3.15.2 using the integrator's existing
environment. This is local evidence only; PR #59, outgoing privacy review,
exact-head Actions and receiving-main integration remain outstanding. Follow-up
`b6d8c57` preserves original hashes for releases without the new fields and
includes reviewed authority in new hashes. Nine affected history/retrospective
tests, focused Ruff and basedpyright pass, including a comparison with the
original PR #59 hash. PR #59 passed its updated head `2ec7251` and merged as
`2b0f78b`; receiving-main CI and Security passed. Its clean worktree and local
branch were retired, and the remote branch was absent. No real-world
retrospective applicability, backpay or cash timing is established.

The source-only retrospective integration branch is now [PR #64](https://github.com/edithatogo/microcosting_healthworkforce/pull/64),
head `795fddc`. Nineteen focused tests, Ruff and basedpyright passed against
current main; all three outgoing commits passed Gitleaks and reviewed Presidio.
Updated head `e34c3e8` passed Actions and Codecov and merged as `6c3fd82`;
receiving-main checks and worktree retirement remain pending.

## Derived component interactions — 6 November 2026

[PR #61](https://github.com/edithatogo/microcosting_healthworkforce/pull/61), commit `cca138a`, adds source-linked ordered fractional dependencies to static and dynamic condition costs, retaining the base ledger and exact additive amounts. Synthetic checks cover an allowance and its incremental superannuation without double counting, parity and expiry during a shift. Local CI passed 176 tests, Ruff, strict basedpyright and Bandit on Python 3.15.2 before rebase; eight affected tests passed after rebase. Outgoing Gitleaks and reviewed Presidio passed; hosted checks and integration are pending. The ACT advanced-skill allowance illustrates the need but individual eligibility, approval, on-cost rates and effective rules remain unverified. Source worktree: `[local worktree]`.

PR #61's updated head `1687aea` passed hosted Actions and merged as `1088ce2`.
Receiving-main CI and Security passed; its clean worktree and local branch were
retired and the remote branch was absent.

The isolated `codex/workforce-retro-derived` worktree combines PR #64's source
with PR #61 and adds `a30f3bb`, requiring separate reviewed retrospective
authority for a derived allowance. Ten focused synthetic tests, Ruff and
basedpyright pass, including static/dynamic parity and failure on missing or
out-of-scope authority. The lane depends on PR #64 and still needs outgoing
privacy review and hosted integration. The source-only successor is [PR #65](https://github.com/edithatogo/microcosting_healthworkforce/pull/65)
at `f56806b`: fourteen focused tests, Ruff, basedpyright, Gitleaks and reviewed
Presidio passed; hosted checks are pending. It does not infer an allowance from
a retrospective salary or determine individual entitlement.

## First-full-pay-period resolver — 6 November 2026

[PR #60](https://github.com/edithatogo/microcosting_healthworkforce/pull/60), commit `74e838a`, resolves an explicitly reviewed first-full-period rule using a complete caller-supplied payroll calendar and source scope. A synthetic dynamic shift verifies that the old and new rates split at the resolved boundary. The retained ACT administrative, support, technical and ambulance editions each contain first-full-period wording at C2.2.2; actual eligibility, payroll boundaries and source selection remain unverified. Local CI passed 176 tests, Ruff, strict basedpyright and Bandit on Python 3.15.2; outgoing Gitleaks and reviewed Presidio passed. PR #60 passed exact-head checks and merged as `8aa4aff`; receiving-main checks are pending. Backpay, cash timing and inferred calendars are not implemented. Source worktree: `[local worktree]`.

## ACT public-sector source batch — 6 November 2026

The [ACT batch review](../../reviews/act-public-sector-source-batch-20261106.md) records six retrieved and hash-verified primary source files with separate candidate SourceRecords. The medical file is a determination with a retrospective variation. The batch review now traces each instrument’s coverage clause and classification schedule, including historical employer wording. Seven held ACT candidates are linked to ten ACT/public screening targets in a versioned 576-row private register; links remain applicability-unassessed. Worker-specific scope, later changes, rights and accepted conditions remain unresolved.

## Knowledge-dated release history — 6 November 2026

[PR #59](https://github.com/edithatogo/microcosting_healthworkforce/pull/59), commit `f47275b`, adds a linear, scope-bound condition release history, explicit knowledge-date selection and content-hash pins for replay. Synthetic static and dynamic cases demonstrate a later-known retrospective correction and unchanged frozen earlier results. Local CI passed 176 tests, Ruff, strict basedpyright and Bandit on Python 3.15.2; outgoing Gitleaks and reviewed Presidio passed. Hosted checks and integration remain pending. Knowledge dates are caller assertions; legal pay periods, backpay, cash timing and real-world source acceptance remain open. Source lane: `[local worktree]`.

## ACT health-professional source — 6 November 2026

The [source review](../../reviews/act-health-professionals-source-20261106.md)
now documents that sequentially indexing the 2022 pay-point gap reproduces all
five published level-3 allowance figures on whole-dollar rounding. This is an
arithmetic hypothesis with retained official sources, not a decision about
author intent, classification transition or worker eligibility.

The [ACT source review](../../reviews/act-health-professionals-source-20261106.md) records a hash-verified official agreement edition, scoped candidate coverage, position-specific weekly hours and a retrospective 2026 correction. A private 32-record successor preserves the previous 17 candidates and adds dated professional-lead table amounts and calculation lineage. The percentages use a separately calculated allowance, not salary; displayed amounts differ from direct percentage arithmetic by up to $0.60 per annum. A separate comparison found that obvious Annex A pay-point differences do not reproduce the Annex C level-3 figure; commencement, payroll and classification-transition basis remain unresolved. Employer/position eligibility, rights and later variations remain unverified; no condition was accepted.

## Northern Territory public-sector discovery — 6 November 2026

The [NT discovery review](../../reviews/nt-public-source-discovery-20261106.md) identifies five official instrument leads and selected approval/operation/nominal-expiry evidence. The selected direct agreement downloads returned HTTP 403, so source bytes, full coverage, variations and individual applicability remain unverified; no NT rates were accepted.

## Queensland applicability cross-check — 6 November 2026

The [historical instrument comparison](../../reviews/qld-workbook-applicability-20261106.md) distinguishes indicative occupational groupings from agreement coverage and the different award relationship for clinical assistants. It identifies the employer, appointment, stream and date evidence needed to resolve the conflicting workbook classification. A separately retrieved 1 September 2022 HPDO award expressly lists medical laboratory scientists and technicians and specifies a 38-hour average ordinary week for covered employees; the workbook uses 36.25 for those two roles. Coverage and denominator intent remain unverified. The later HP agreement also lists these disciplines; the general award's 36.25-hour pathology provision has specific employment and continuity conditions. Four workbook rows use 36.25 hours; a 38-hour comparison changes their hourly denominator by about 4.83%, holding annual cost fixed. No individual entitlement is inferred.

## Candidate profile availability — 6 November 2026

[PR #58](https://github.com/edithatogo/microcosting_healthworkforce/pull/58), commit `0691e0c`, packages and loads the hash-bound 262-section provisional profile. Its integration test assigns all 27,929 populated cells and retains the empty sheet without accepting historical values. Full local CI passed 168 tests on Python 3.15.2 before rebasing, and the profile loaded from an extracted wheel; wheel and source distribution both contain the metadata. Outgoing Gitleaks and reviewed Presidio passed. PR #58 passed exact-head checks and merged as `3740785`; receiving-main CI and Security passed. Its clean worktree and local branch were retired; the remote branch was already absent. Candidate units and source applicability still require semantic qualification.

## Candidate semantic type audit — 6 November 2026

The [ALL component basis review](../../reviews/workbook-all-component-basis-20261106.md)
checks 40 primary-workbook formulas that average jurisdiction inputs and multiply
them by the first jurisdiction's salary. All 31 nonzero comparisons differed
from the alternative unweighted mean of jurisdiction-specific components; nine
were zero in both. Preserve the original basis and flag the choice for semantic
review rather than assuming either aggregation represents intended practice.
The source-only branch `codex/workforce-all-component-basis`, commit `0715862`,
now encodes that salary basis and the separate fixed-allowance and salary means
in the candidate profile. A focused test checks all 60 ALL formulas and their
roles. Four profile tests, Ruff and basedpyright passed on Python 3.15.2.
Outgoing Gitleaks and reviewed Presidio also passed; [PR #67](https://github.com/edithatogo/microcosting_healthworkforce/pull/67)
is open with hosted checks and integration pending.

The isolated `codex/workforce-component-lineage` branch at `d754551` maps ten
primary-workbook amount and share blocks to named historical components and
identifies lower and upper salary bounds as alternatives. A focused test
verifies all 600 exact source formulas across 25 jurisdiction-role rows and
their candidate units and meanings. Three profile tests, focused Ruff and
basedpyright passed locally on Python 3.15.2. The formulas describe workbook
proxies and midpoint-cost denominators; they do not accept actual entitlements
or resolve the other semantic sections. The source-only lane still needs
integration, privacy review and exact-head Actions.

The source-only packet was cherry-picked onto current main in isolated branch
`codex/workforce-component-integration` at `c339950`; focused profile tests,
basedpyright and outgoing Gitleaks passed. Presidio's 223 PERSON flags were
reviewed as workbook metadata, coordinates, model terms or retained copyright
attribution; positive controls passed. [PR #63](https://github.com/edithatogo/microcosting_healthworkforce/pull/63)
passed its updated head and merged as `9e9ae85`; receiving-main CI and Security
passed and both clean source/integration worktrees and branches were retired.
The same patch was also committed
as `1cbd6f4` in the Conductor checkout; avoid reintegrating it there.

The [candidate unit audit](../../reviews/workbook-candidate-unit-audit-20261106.md) identified and corrected 120 formatted component values and 16 repeated comparison headers that had numeric units attached to literal text. The retained 262-section successor covers all 27,929 populated cells with no literal-text/unit findings. A separate trace checked all 120 publication-comparison formulas and identified both BI and BS display labels as references to the bioinformatics numerator block; original labels are retained. These are narrow checks, not complete semantic or entitlement acceptance.

## Archived sensitivity mapping — 6 November 2026

[PR #55](https://github.com/edithatogo/microcosting_healthworkforce/pull/55), source commit `206a654`, adds reviewed-hash candidate mappings for 7,139 populated cells in four long-form archived sheets. Annual and hourly values, identities and source cells are preserved; PSA-labelled historical bounds are not probabilistic draws. All 330 rows of the paired hourly archives match by source cell values. Full local CI passed 159 tests, Ruff, strict basedpyright and Bandit on Python 3.15.2; outgoing Gitleaks and reviewed Presidio passed. PR #55 passed exact-head checks and merged as `35bf409`; receiving-main CI and Security passed. Its clean worktree and local branch were retired; the remote branch was already absent.

## Medicare weighting mapping — 6 November 2026

Isolated worktree `[local worktree]`, branch `codex/workforce-weight-mapping`, commit `fb95baa` (rebased from `cdf3e7c`), maps all 263 populated cells in the Medicare enrolments and weighting sheets with original lineage. Card counts, persons, persons per card, the five-state denominator and fractions are distinct; a historical system-change quantity remains explicitly unresolved. The mappings require the reviewed workbook hash and do not accept enrolments as workforce weights. Four focused tests and full local CI (157 tests, Ruff, strict basedpyright and Bandit on Python 3.15.2) passed before rebasing. Gitleaks and reviewed Presidio screening passed for the outgoing commit. [PR #54](https://github.com/edithatogo/microcosting_healthworkforce/pull/54) passed Actions and merged as `4e7e162`; its Codecov patch check subsequently passed, as did receiving-main CI and Security. The clean worktree and local branch were retired; the remote branch was already absent.

## Component worksheet mapping — 6 November 2026

Isolated branch `codex/workforce-component-mapping`, commit `1701ba3` (rebased from `e8a487f`), maps
the 870 populated cells in `Components $ and %` as jurisdiction dollar values,
shares, and separate formatted ALL rows. The mapping requires the reviewed
workbook SHA-256 and preserves cell lineage and candidate status. Four focused
workbook tests and the full local CI (157 tests, Ruff, strict basedpyright and
Bandit) passed on repo-local Python 3.15.2 before the source-only rebase.
Outgoing commit Gitleaks and Presidio checks passed after review. [PR #53](https://github.com/edithatogo/microcosting_healthworkforce/pull/53) passed all hosted checks and merged as `3ea04f0`; receiving-main CI and Security passed. The clean worktree and local branch were retired; the remote branch was already absent; this does not complete semantic mapping or
accept historical values as entitlements. The isolated worktree is
`[local worktree]`.

## Comparative costing templates — 6 November 2026

Restricted NSW and Queensland costing workbooks provide candidates for a
component and interaction comparison: pay-point progression, roster and
overtime, leave backfill, allowances and on-costs. The Queensland copies also
distinguish FTE and headcount. Their formulas and rates have not been qualified
for this library; compare source-specific assumptions and effective dates with
the versioned model before implementing or asserting parity. Exact source
identities and hashes are retained outside tracked files.

## Hosted CI download timeout — 6 November 2026

Static-costing PR #52 had two terminal CI attempts cancelled at the 20-minute job limit while downloading LibreOffice from the Ubuntu mirror; neither reached the test step. [PR #57](https://github.com/edithatogo/microcosting_healthworkforce/pull/57), commit `e7a4de8`, raises the job timeout to 60 minutes without removing the loader, tests or existing gates. Actionlint and outgoing Gitleaks/Presidio review passed. PR #57 passed exact-head checks and merged as `df49675`; receiving-main CI and Security passed. Its clean worktree and local branch were retired; the remote branch was already absent. Other jobs with the original timeout are updated after their terminal status.

## Capped daily overtime adjustment — 6 November 2026

[PR #56](https://github.com/edithatogo/microcosting_healthworkforce/pull/56), source commits `5f9101b` and `bdb8f48`, introduce explicit daily tier and hourly cap arithmetic that subtracts salary already included in the base ledger and permits a signed adjustment. Synthetic checks reproduce the $260 worked example, negative adjustment, tier history and segmentation, and reject uncovered or unsupported inputs. Six focused tests also check unchanged allowance and salary-fraction components and reject unreviewed or out-of-date rules. Local CI passed 161 tests at `5f9101b`, Ruff, strict basedpyright and Bandit on Python 3.15.2; outgoing Gitleaks and reviewed Presidio passed. PR #56 passed its exact-head hosted checks and merged as `4dca1d1`; receiving-main CI and Security passed. Its clean worktree and local branch were retired; the remote branch was already absent. Eligibility, historical award applicability, holiday/recall interactions, rounding and time-off choices remain unresolved; this method does not implement the full SA award.

## SA scientist overtime rule gap — 6 November 2026

The [source-backed overtime review](../../reviews/sa-scientist-overtime-capability-20261106.md)
identifies daily tiers, an MS2 salary cap, calendar and recall interactions,
rounding and time-off choices not represented by the current cumulative method.
A hand-calculated example demonstrates the signed adjustment needed when base
pay has already been counted. These are outstanding capabilities, not an
accepted real-worker rule.

## South Australian historical salary reconciliation — 6 November 2026

The [SA source comparison](../../reviews/sa-2022-workbook-source-reconciliation-20261106.md)
visually checks four scanned salaried-agreement schedules and separately the
medical-scientist award minimum. Workbook endpoints are close but not identical;
two upper labels differ from the selected close classifications. Applicability,
source intent and individual applicability remain unresolved. The dated 2022 medical-officer schedules were visually compared; their salary-sacrifice schemes differ and neither matches the workbook endpoints exactly. A 2022-named AGD URL delivered a 2025-labelled document and is not used as 2022 evidence.

## Queensland EB11 salary reconciliation — 6 November 2026

The [EB11 source trace](../../reviews/qld-eb11-workbook-reconciliation-20261106.md)
links Queensland laboratory and administrative endpoints to the certified
agreement's 1 September 2022 schedules. Identical laboratory amounts occur in
multiple streams; worker scope and the 2023 certification/2022 wage-date
distinction remain explicit. Practitioner-row amounts match General Employees professional Level 2–6 reference salaries, while the HP2–HP3 label belongs to a different health-practitioner scale; worker applicability remains unresolved. The Queensland medical-officer upper workbook endpoint matches L29 in a 2023 reprint, while its grade label ends at L27; dates and individual applicability remain separate.

## Static condition snapshot — 6 November 2026

Source commit `36f0c7e` adds a nominal-hours static snapshot for the versioned
annual-salary conditions method. It returns scoped component totals, exact
rational total and the accepted condition/source citations used. Synthetic
checks demonstrate parity with a constant-date activity, an exact nonterminating
rate, zero and invalid quantities, and uncovered dates. Local Python 3.15.2
validation passed 158 tests, Ruff, strict basedpyright and Bandit. Integration
preflight and full outgoing Gitleaks/Presidio review passed. [PR #52](https://github.com/edithatogo/microcosting_healthworkforce/pull/52)
had two CI attempts cancelled during Ubuntu package downloads. After updating onto the longer timeout, PR #52 passed exact-head checks and merged as `49c6a26`; receiving-main CI and Security passed. The clean source worktree and local branch were retired; the remote branch was already absent. No overtime, leave, cover or real-world eligibility
is inferred; the broader static/dynamic and source tracks remain open.

## NSW historical salary reconciliation — 6 November 2026

The [NSW 2022 review](../../reviews/nsw-2022-workbook-source-reconciliation-20261106.md)
records recovery of the previously unavailable official gazette and matches
both endpoints for the laboratory and scientist workbook rows to specific
salary tables. Individual classifications, employer and pay-period applicability
remain unresolved; the historical matches are not accepted entitlements. A further bioinformatics candidate matches a restricted transferred-staff table across different 2021/2022 rate columns; its source and applicability remain unresolved. Administration endpoints also match different pay-period columns in a 2022 award; the staff-specialist upper amount matches Senior rather than the labelled level 5. These are candidate matches, not individual applicability. A 2022 Hospital Scientists clause supports a 38-hour average for its ordinary-hours measures; the workbook bioinformatics row records 40, with basis and coverage unresolved. Technical and administrative candidates also have 40-hour inputs versus a conditional 38-hour roster average under their incorporated 2022 conditions award; individual roster basis remains unresolved. Nine original hourly formulas directly divide by the 40-hour inputs; a 38-hour denominator would increase those outputs by 5.26% with annual cost held constant, a sensitivity only.

## Component summary mapping — 6 November 2026

The [component summary trace](../../reviews/workbook-component-summary-lineage-20261106.md)
maps both table orientations, checks 55 numeric fields against their five
jurisdiction inputs and the `ALL` formulas, and preserves salary ranges as
display text. A versioned private profile assigns all 27,929 populated cells
across 260 candidate sections; this does not complete other semantic mappings
or qualify historical values as entitlements.

## Explicit activity allocations — 6 November 2026

Isolated source commits `fca3f5a` and `c0e1c37` add optional opaque allocation
identities to flat-hourly activities and cost rows. The dynamic method rejects
overlapping activities for an explicitly identified worker, including across
rate categories, while preserving parallel aggregate category costing when no
identity is supplied. Complete detection requires the caller to identify all
activities for that worker; no identities or availability are inferred.

Source commit `8e1353b` additionally rejects distinct or partially identified
workers in one overtime period, including tiered overtime through its shared
primitive. The full local suite passed 155 tests on Python 3.15.2 at that
commit, alongside Ruff, strict basedpyright and Bandit. Integration preflight,
Gitleaks and reviewed Presidio passed. [PR #51](https://github.com/edithatogo/microcosting_healthworkforce/pull/51)
passed all exact-head checks and merged as `5ccb214`. Receiving-main CI and
Security passed; the private scan receipt was retained and the merged worktree
and local branch retired. The remote branch was already absent. This does not implement rostering capacity,
industrial eligibility, source resolution or all costing interactions.

## Interaction ledger continuation — 6 November 2026

Source commit `fea7457` in the isolated `codex/workforce-interaction-ledger`
lane retains the complete minimum-engagement and overtime results inside the
combined result, including activity, condition and segment provenance. The full
local suite passed 152 tests on Python 3.15.2 using the qualified existing
dependencies; affected Ruff checks, strict basedpyright and Bandit passed. Source-packet preflight, Gitleaks and reviewed Presidio passed;
[PR #50](https://github.com/edithatogo/microcosting_healthworkforce/pull/50)
passed exact-head checks and merged as `a2b396e`; receiving-main CI and
Security passed. The private scan receipt was retained and the merged source
worktree and local branch were retired; the remote branch was already absent.
It does not qualify the source applicability or other interaction methods.

## Workbook weighting trace — 6 November 2026

The [coordinate-level weight trace](../../reviews/workbook-weight-lineage-20261106.md)
verifies the eight copied enrolment counts, five selected weights and ten
weighted midpoint formulas against the unchanged original workbook. This
qualifies their historical lineage, not the weighting assumption or other
semantic mappings.

## Source integration — 6 November 2026

The bounded implementation through `073c3d3` was integrated by
[PR #46](https://github.com/edithatogo/microcosting_healthworkforce/pull/46),
merged as `5e82c56`. Exact-head checks and receiving-main CI and Security passed;
local `make ci` passed 142 tests on Python 3.15.2. The integrator reconciled
completed ownership and raw-intake subtasks with their receipts. This merge does
not complete semantic qualification, an accepted condition release, general
rule interactions, or the remaining source and applicability work.

## Latest exact-costing checkpoint — 6 November 2026

The [exact-costing continuation](../../reviews/workforce-v2-exact-costing-20261106.md)
records source commits `00db1e5` and `d266c98` and a full `make ci` pass with
139 tests on Python 3.15.2. Source commit `073c3d3` subsequently extended exact
totals and input revalidation to flat-hourly costing; full `make ci` passed
with 142 tests. Source applicability,
semantic acceptance and unimplemented rule interactions remain open; both tracks
remain in progress.

## Latest source and parity review — 6 November 2026

The [source and parity review](../../reviews/workforce-v2-source-and-parity-20261106.md)
records the retained Victorian scientist agreement, a specific workbook
RX4/RX1 conflict, and further archived sensitivity-bound comparisons. Source
commit `dc3ff70` adds exact rational condition-activity totals; `make ci` passed
with 135 tests on Python 3.15.2. Grade intent, source applicability, workbook
bound semantics and remaining cost-rule interactions are unresolved; both tracks
remain in progress.

## Current review — 6 November 2026

The [mapping/source/rules review](../../reviews/workforce-v2-review-20261106.md)
records 248 candidate workbook sections, a reproducible archive comparison,
additional NT/TAS discovery leads and 403 access outcomes, and source commit
`872ef9b` and `300b8b7` for explicit overtime tiers and a bounded minimum
engagement rule. `make ci` passed with 133 tests on Python 3.15.2. Candidate semantic mappings, source applicability and further
costing-rule interactions remain open; neither track is complete.

## Latest continuation — 6 November 2026

The [continuation review](../../reviews/workforce-v2-continuation-20261106.md)
records the 240-section candidate workbook profile, targeted Queensland agreement
extraction, historical NSW acquisition timeout and source commits `30da372`
and `f9fdb44` for bounded cumulative overtime and explicit paid-capacity
scenarios. Full `make ci` passed with 127 tests on Python 3.15.2. One isolated
workbook cell is explicitly unresolved and broader
semantic, applicability and costing-rule qualification remains open. Neither
track is complete and no accepted national condition bundle is implied.

## Continuation receipt — 6 November 2026

Source commits `87d08a7` and `b63014f` add a separate v2 CLI, explicit table
segmentation, candidate condition
releases, limited annual-salary rules, dated activity costing and scoped source
gap screening. The full repository `make ci` passed on Python 3.15.2 with 120
tests; a later CLI gate passed with 121 tests and a synthetic installed-wheel
CLI run outside the source checkout. The private [implementation review](../../reviews/workforce-v2-implementation-20261106.md)
records extraction reconciliation, the initial NSW instrument batch, remaining
semantic/source gaps and boundaries. Both tracks remain in progress; raw or
keyword discovery coverage is not reviewed economic or industrial coverage.

## Implementation receipt — 6 November 2026

Source commit `3622856` in the isolated `codex/workforce-costing-v2` worktree
adds raw workbook cataloguing, source evidence contracts and explicit static and
activity-based `flat_hourly_v1` costs. On the original workbook, intake independently
matched 20 sheets, 27,929 nonempty cells, 94 physical regions and 9,299 formulas
with absent caches; the input SHA-256 was unchanged. This is raw inventory, not
semantic table incorporation or recalculated formula results. The new method
rejects unsupported rules and uncovered dates; it does not interpret awards,
calculate overtime or leave, or establish a real-world condition release.

`make ci` passed on Python 3.15.2: formatting, lint, strict type checking, 111
tests and Bandit. Synthetic tests cover source qualification, source byte hash,
exclusive evidence horizon, static/dynamic agreement, rate-boundary splitting
and missing coverage. The existing calculator and PSA assumptions are unchanged.
The CLI, semantic mappings, accepted condition release and planned rule families
remain to be implemented and qualified.

## Starting evidence, ownership and release boundaries

Read the [approved specification](./spec.md), [source-coverage plan](../workforce-source-coverage_20261106/plan.md)
and canonical [workflow](../../workflow.md). Qualified main is 11df8b3, with 100
tests on Python 3.15.2. Original workbook hashes, the 20-sheet/94-region register,
9,299 absent formula caches, one sheet-local name, and source/assumption gaps are
already documented. Reuse unchanged parity/package/CLI receipts with exact blob
checks; do not repeat the former migration review or GHA native replays.

The integrator owns dependency/runtime promotion, main and Conductor. Implement
source in a separately owned clean worktree. Proposed modules/interfaces below
are responsibilities to resolve against the actual checkout, not files already
implemented. Preserve original CLI behaviour, workbook/configuration editions,
GHA reporting/scenario ownership and genomics independence.

Keep three versions distinct: schema version, immutable condition-data release,
and costing-method version. Raw or workbook-reported candidate data is not an
accepted primary-source entitlement release. Private source documents, extracted
real-world values and receipts must not enter public source distributions.

## Phase 0: Freeze contracts and establish scoped implementation

- [x] Task: Pin the implementation packet and inherited evidence.
  - [x] Inspect actual worktrees, branch/dirty/staged paths, ownership and active
    operations; create/select the isolated source lane and record scope.
  - [x] Verify actual repo-local Python 3.15.2 and locked package identity; preserve
    existing environments until their operations reach a terminal checkpoint.
  - [x] Hash original workbook/configurations and legacy numerical-core blobs;
    inventory current API/CLI/output contracts and baseline evidence to reuse.
- [ ] Task: Define schemas and acceptance boundaries before coding.
  - [ ] Write the raw-cell, semantic-table, source-citation, condition, release,
    quantity/event and cost-ledger contracts with explicit units and identity keys.
  - [ ] Define accepted versus candidate/unresolved release states, cost perspective,
    paid/productive capacity, unknown/zero/not-applicable semantics and failure modes.
  - [ ] Assign module/test responsibilities without duplicating the source register
    or the modernization track's performance/reader experiments.
- [ ] Task: Phase Verification & Checkpoint (refer to ../../workflow.md).
  - [ ] Inspect inherited receipts and contract examples; record exact scope,
    source dependencies and unresolved scientific choices without changing priors.

## Phase 1: Lossless workbook/configuration intake

- [ ] Task: Write failing intake and integrity tests first.
  - [ ] Cover all 20 sheet identities, 94 regions, 27,929 nonempty-cell inventory,
    empty/label-only regions, merged headers, formulas, missing caches, hyperlinks
    and the sheet-local IDX name. Treat these as pinned-workbook expectations,
    not universal dimensions for future editions.
  - [ ] Cover changed-sheet/header/shape rejection or explicit new-edition intake,
    source-byte preservation, duplicate cells and exact source-coordinate lineage.
  - [ ] Use small synthetic fixtures publicly; keep original-workbook assertions
    and derived values in the existing private qualification lane.
- [~] Task: Implement bounded raw intake and manifest export.
  - [x] Use current openpyxl/Polars contracts; preserve raw literals/formulas and
    cached-value state without saving the original or filling unknowns with zero.
  - [x] Record workbook/configuration/source hashes, headers/names/links and cell
    provenance in portable private artifacts; no parallel generic document system.
  - [ ] Use the retained copy/recalculation route only if evaluated results are
    needed, with one native owner and a frozen readback consumed by verifiers.
- [~] Task: Reconcile every physical region and raw configuration record.
  - [ ] Map all cells once to source inventory; report uncovered, duplicated or
    newly introduced regions as explicit discrepancies.
- [ ] Task: Phase Verification & Checkpoint (refer to ../../workflow.md).
  - [ ] Review original-byte/hash preservation and selected raw/formula/empty cases;
    run exact affected tests and full gates at the code milestone.

## Phase 2: Semantic tables and complete parameter/assumption extraction

- [ ] Task: Write failing semantic mapping and unit tests first.
  - [ ] Cover primary/source metadata, Year 0–4 outputs, ALL and WM variants,
    component dollars/shares, Medicare data/method notes and assumptions.
  - [ ] Cover DSA inputs and wide/long/publication outputs, PSA-labelled archived
    bounds, fixed-header inputs, summaries, empty percentage sheet and scalar archive.
  - [ ] Cover 1.5 versus 0.015 indexation, currency under reused percentage labels,
    display versus numeric columns, state/order variants and duplicate identities.
- [~] Task: Implement typed semantic tables with explicit archive status.
  - [ ] Split adjacent/stacked semantic subtables beyond the physical-row regions;
    attach schemas, identity keys, units, roles and source-cell/formula lineage.
  - [ ] Keep nominal/weighted/component variants separate. WM midpoints are weighted;
    MIN/MAX bounds and 95% CI display labels are not new statistical intervals.
  - [ ] Preserve original DSA baseline/axes and all 17 false archived diagnostics;
    do not relabel them as passing checks or force both signs onto one midpoint.
  - [ ] Capture every old JSON parameter/formula/distribution and workbook condition/
    assumption with a candidate v1-to-successor disposition, not silent defaults.
- [~] Task: Document and qualify complete semantic incorporation.
  - [ ] Reconcile semantic coverage to all 20 sheets/94 regions and record the
    original Year 0–4 versus current default Year 0–5 horizon distinction.
  - [ ] Export lossless candidate records privately; do not promote archived,
    conflicting or workbook-reported values to accepted entitlements.
- [ ] Task: Phase Verification & Checkpoint (refer to ../../workflow.md).
  - [ ] Manually trace representative tables/units/aggregates back to exact cells;
    retain unresolved semantics and independent source acceptance boundaries.

## Phase 3: Source-backed condition registry and immutable successor bundle

- [~] Task: Write failing condition/release contract tests before implementation.
  - [ ] Cover source/hash/citation identity, employer/classification applicability,
    currency and units, genuine zero versus missing, overlap/gap and conflict rejection.
  - [ ] Cover separate approval/commencement/pay-effective/knowledge dates,
    pay-period qualifications, retrospective changes and nominal expiry handling.
  - [ ] Cover declarative rule interactions, caps, exclusions and unsupported rules;
    no arbitrary code/eval from documents or uploaded configuration.
- [ ] Task: Re-extract relevant verified source batches from the acquisition track.
  - [ ] Extract salary/pay points, ordinary hours/employment fractions, leave/loading,
    superannuation, penalties/overtime, on-call/recall/minimum engagements, allowances,
    progression and date rules with exact clause/page/table evidence.
  - [ ] Preserve original wording/context privately, verify OCR against the page
    where needed, and record method/reviewer/uncertainty and ambiguous eligibility.
  - [ ] Reuse frozen GHA evidence after hash/rights checks; category-specific QLD
    development allowance and WA Arrangement A evidence do not establish universal
    eligibility. No empirical prior/dependence calibration is inferred.
  - [ ] Keep entitlements, observed utilisation, analyst assumptions, statistical
    weights and uncertainty distributions as different typed record classes.
- [ ] Task: Build the versioned successor candidate and accepted-subset machinery.
  - [ ] Freeze schema/data/method versions, manifests, lineage and complete v1-to-v2
    changes; never overwrite earlier inputs/releases or silently revise a published ID.
  - [ ] Admit only verified applicable records to an accepted costing subset;
    retain unknown/unverified/unsupported conditions in candidate/gap outputs.
  - [ ] Define correction, supersession and reproducible rollback/re-selection
    without implying nationwide source completion or accepting unresolved assumptions.
- [ ] Task: Phase Verification & Checkpoint (refer to ../../workflow.md).
  - [ ] Independently inspect sampled and material numeric/rule citations and full
    release diffs; report source verification separately from model-method acceptance.

## Phase 4: Static snapshot and quantity-based microcosting

- [ ] Task: Write failing static costing contracts and economic examples first.
  - [ ] Cover explicit accepted release/date/employer/classification selection,
    missing/overlapping coverage, unit mismatches, positive/zero quantities and rounding.
  - [ ] Demonstrate independently calculated component costs and proportional
    quantity scaling; distinguish annual/weekly/hourly and per-activity units.
  - [ ] Retain nominal-hours baseline and paired productive-capacity/leave-cover
    examples with no salary/cover double counting; compare compatibility mode
    against unchanged legacy results with explicit tolerance and source identity.
- [~] Task: Implement the static library interface and auditable output ledger.
  - [ ] Separate explicit resource quantities, accepted unit prices, component
    rules, paid cost and productive capacity; emit totals, currency/price date,
    method/release/source lineage and diagnostic decisions.
  - [ ] Reuse the existing legacy calculation through an explicit compatibility
    adapter; introduce no silent change to its defaults, direct outputs or priors.
  - [ ] Reject unresolved v2 inputs rather than applying legacy zero/neutral fallbacks.
- [ ] Task: Qualify the static interface with source-backed and synthetic cases.
  - [ ] Classify every successor difference as extraction, unit, effective-date,
    formula or declared method change. Do not tune parameters to recover old costs.
- [ ] Task: Phase Verification & Checkpoint (refer to ../../workflow.md).
  - [ ] Inspect component-ledger arithmetic and source traces, targeted properties
    and applicable full checks; retain any unresolved method/coverage blockers.

## Phase 5: Effective-dated activity/roster dynamic costing

- [ ] Task: Write failing temporal/rule-state tests before implementation.
  - [ ] Cover wage/condition/classification/FTE transitions, uncovered/overlapping
    dates, pay-period boundaries, overnight shifts, explicit local calendars/timezones
    and duration/quantity units. Calendar/holiday inputs are versioned, not guessed.
  - [ ] Cover ordering, cumulative overtime/eligibility history, exclusive/stacked
    rules, minimum engagements and state carry-over where the accepted rules need it.
  - [ ] Check constant-rate/date reduction to static costing and segmentation/
    aggregation invariance where no threshold or approved rounding changes the result.
- [~] Task: Implement the deterministic dynamic costing interface.
  - [ ] Split activity/resource segments at relevant boundaries and apply selected
    accepted rules in a stable chronological order; require necessary prior history.
  - [ ] Keep retrospective wage entitlement, pay-effective period and cash/backpay
    timing distinct according to explicit cost perspective; do not silently reprice
    an uncovered period or apply knowledge from a later release to a frozen run.
  - [ ] Emit event/time/resource/component ledgers with exact rule/source versions;
    allow fixed-quantity price scenarios and changed quantities/rosters separately.
  - [ ] Validate duplicate/overlapping resource allocations where the input contract
    requires it. Use synthetic opaque identities; no patient/staff data acquisition.
- [ ] Task: Qualify dynamic results independently of stochastic uncertainty.
  - [ ] Demonstrate simple hand-calculated dated activities and nontrivial rule
    boundaries; report unsupported rules as capability gaps rather than approximating
    them with an undocumented average multiplier.
- [ ] Task: Phase Verification & Checkpoint (refer to ../../workflow.md).
  - [ ] Review temporal splits, state transitions, totals and provenance; retain
    failing boundary cases and verify no hidden quantity/cash-saving assumptions.

## Phase 6: API/CLI integration, scenarios and documentation

- [ ] Task: Write failing public-interface integration tests first.
  - [ ] Cover explicit static/dynamic selection, input/release/method paths, invalid
    requests, output lineage and unchanged default legacy CLI behaviour.
  - [ ] Verify new scenario wrappers call the same selected cost function; keep PSA
    optional and do not silently change old seeds, priors, dependence or estimand.
- [~] Task: Expose supported library and bounded CLI interfaces.
  - [ ] Document all-input/accepted-release requirements, quantity and price units,
    capacity/leave-cover perspective, date/rule failures and immutable run identity.
  - [ ] Provide synthetic static and dynamic examples, source/condition dictionaries,
    migration instructions, v1/v2 differences and unsupported-rule/source gaps.
  - [ ] Cross-link source acquisition, workbook intake, modernization and GHA
    evidence without replacing their ownership or duplicating native mutations.
- [ ] Task: Phase Verification & Checkpoint (refer to ../../workflow.md).
  - [ ] Inspect actual CLI outputs/examples and API errors; confirm every sheet's
    disposition and every candidate/accepted distinction is documented truthfully.

## Phase 7: Installed qualification, source-only integration and handoff

- [ ] Task: Run coherent final verification without weakening existing gates.
  - [ ] Run affected/full strict tests, coverage, format/lint/type/security and
    applicable mutation checks; retain cacheprovider and default zero retries.
  - [ ] Build/inspect wheel and sdist for source/licence correctness and absence
    of real documents, values, private receipts or raw workbook payloads.
  - [ ] Exercise installed static/dynamic/legacy APIs and CLI outside the checkout.
    Arrange owner-run original-workbook parity only for changed numerical paths;
    otherwise reuse exact unchanged source/runtime/native evidence with attribution.
- [ ] Task: Freeze candidate/accepted releases and source-integration packet.
  - [ ] Record release/source/configuration/runtime identities, changed scope,
    acceptance evidence, rollback/re-selection and all unresolved source/scientific
    conditions. Technical completion does not imply a nationally complete dataset.
  - [ ] Run source-integration preflight and full outgoing-range privacy review;
    merge only after exact-head Actions, then verify receiving main before pruning.
- [ ] Task: Phase Verification & Checkpoint (refer to ../../workflow.md).
  - [ ] Deliver one terminal handoff, update both tracks and the modernization
    dependency map, and retain blocked source/method tasks instead of false completion.

## Dependencies, safe parallel progress and stop conditions

Raw/semantic intake and schemas can proceed while sources are acquired. Accepted
conditions are gated per verified source batch. Static contracts precede dynamic
execution; documentation and independent source acquisition can proceed alongside
bounded implementation in separately owned lanes. Source-access/identity failures
block only dependent records; they do not justify speculative values or broad
access changes. Unsupported rule semantics and unapproved priors/weights remain
explicit acceptance blockers, not reasons to discard technical progress.

## Skill review

No missing Firebase/GCP skills match the approved Python/data/costing scope.
No skill installation or environment refresh is required. Existing document and
spreadsheet skills are used only when their actual extraction tasks begin; the
integrator retains runtime/dependency and shared Conductor ownership.

## Storage interruption — 6 November 2026

Continuation was interrupted by ENOSPC while creating a rule-interaction module; pytest could not create temporary files. The incomplete untracked test was removed and no new source change or passing validation is claimed. Both data volumes remain nearly full. See [ownership](../../ownership.md) for the exact recovery boundary. Recheck writable free space before resuming.

## Additional budgeting comparison — 6 November 2026

Compare the discovered restricted templates' costing categories and time bases
with this track's rule model using synthetic fixtures and source-backed decisions.
Structural discovery is not rule extraction or parity. See [template discovery](../../reviews/workforce-budget-template-discovery-20261106.md).

## Queensland dependent dropdown reconciliation

Both retained editions use a named blank fallback in the list validation
guard when dependent inputs are populated. The Labour edition has six
populated targets on this branch. Four of those targets are populated
in the FTE edition and resolve to the same guard. Preserve their stored
selections and the original rule. The blank fallback represents a guard
branch, while normal grade and award options are selected separately.

An isolated synthetic Calc replay distinguished the trailing-comma
VLOOKUP form from the three-argument form. The trailing-comma result
matched explicit zero in the probe. Applying that behavior to cached
values yields three provisional members in Labour and two in FTE
among the previously unresolved cases. Keep those dispositions
provisional pending native Excel lookup and manual-entry verification.
Private lineage v3 retains the original rule evidence and both review
dispositions by edition.

## Static, dynamic and CLI implementation checkpoint

At main 034ae07, the library exposes static and dated activity pricing,
assignment snapshots and activity ledgers, productive capacity costing,
and explicit roster overtime. The v2 CLI dispatches reviewed requests.
The focused costing, assignment, capacity, roster and CLI suites pass.
These checks cover the implemented contracts and synthetic cases.
Full source-backed releases, remaining rule interactions, workbook
runtime verification and final package acceptance remain open.

## Installed package checkpoint

At cc7e809, a wheel built from the source distribution contained 81 source
members matching the checkout byte for byte. Both archives carried the
licence and excluded workbook and PDF inputs. The wheel metadata declared
Apache-2.0. A fresh Python 3.15.2 environment installed the source
distribution and its 25 dependencies from the retained offline cache.
The dependency check passed.

Outside the checkout, the installed v2 CLI produced the expected synthetic
snapshot and dated-activity totals. The installed legacy CLI ran with
explicit external workbook and configuration inputs. Its base case, DSA
summary and detail, archived comparison and validation outputs matched
the source run byte for byte on the same interpreter and inputs.
This checkpoint qualifies the tested revision and retained dependency
cache. Native Excel behavior, source applicability and final release
acceptance remain open.

The 17 delivered validation diagnostics still report differences above a
cent. Identical diagnostics establish package parity for the tested outputs.
The archived workbook discrepancies retain their separate dispositions.

## DSA validation evidence boundaries

The installed-package run at cc7e809 passed 20 live scenario checks,
covering 500 state-role comparisons, with a maximum absolute difference
of about 5.82e-10 AUD. The live oracle changes workbook inputs and
recalculates the scenario before comparison.

The archived diagnostic reads the delivered DSA Values sheet. Direct
inspection confirmed that each of the nine matched column groups selects
its MP column. The Leave Loading (%) group is present at BK1 with two trailing tabs.
The legacy exact match skips both variants. The archive mapping can
identify that group by its reviewed coordinate and preserve its raw label. Preserve the
17 existing archived flags and the unmatched mapping as historical
evidence. Neither represents a failure of the live scenario oracle.

## Workbook and contribution validation checkpoint

The pinned historical workbook extraction assigns every populated cell
across 267 sections and 20 sheets, including one empty sheet. The isolated
AK39 zero stays outside costing inputs. AK34 stays missing in the extracted
bound. PRs #228 and #229 document the mapping and the independent replay of
all 300 aggregate DSA outputs against a private LibreOffice recalculation.
The evidence qualifies historical arithmetic. The scientific provenance of
the bounds remains open.

The Queensland vehicle diagnostic reconciled 96 downstream outputs over
24 positive vehicle months. PR #226 documents the historical bases and
the dated applicability questions. PR #227 tests the comparison of two
paid-earnings bases using synthetic postings. The actual payroll component
mapping is still required for a source-backed release.

The [primary component replay](../../../docs/workbook_primary_components.md)
matched 600 jurisdiction-role outputs, 60 aggregate amounts and 60 formatted
aggregate shares against the private recalculation. The workbook uses the
first jurisdiction's midpoint cost in the aggregate share displays.
The intended interpretation as a national aggregate remains open.

The [publication comparison replay](../../../docs/workbook_publication_dispositions.md)
matched all 120 ratios against the private recalculation within an absolute
difference of 0.000000000001. The formula-derived personnel roles and original
display labels remain separately traceable. This validates the ratios given
their scenario costs. It does not qualify the underlying sensitivity bounds.

The [archived PSA reference](../../../docs/workbook_aggregate_inputs.md)
was introduced in `8bb90f9` and retains its original value. The
introducing validator used an unweighted mean of result-row means.
The scalar remains a historical reference with unresolved generating
method and unit. Scientific PSA qualification remains separate.

### Contribution release evidence

Paid contribution pricing now preserves assignment identity and earning
intervals separately from posting dates. PRs #231–#233 verify those boundaries
and the shared source scope. PR #238 verifies that zero payments still require
valid factor evidence. This supports static and dynamic calculation checks
with synthetic inputs.

For a Queensland vehicle release, the next acceptance input is a dated
payroll example linking the assignment, earning interval, payment date and
component code to the applicable superannuation and levy bases. Where the
HHS receives a service recharge, verify the dated recharge schedule instead
of applying a direct insurer premium to that HHS ledger. Preserve the
historical workbook calculation under its own basis.

The [historical weighting replay](../../../docs/workbook_medicare_method_change.md)
matched all 17 normalisation outputs and ten weighted annual and hourly
labour costs. The cost formulas use the column H series. The evidence
establishes the workbook's arithmetic and selected denominator. Using
these weights for workforce estimates still requires evidence that the
underlying population represents the workforce being costed.

PR #242 adds a quarterly long-service leave levy deadline calculator.
It counts 12 working days after calendar quarter end using explicit daily
classifications and rejects missing dates. The March and September 2026
Queensland holiday scenarios yield 20 April and 19 October respectively.
Main CI and Security passed at 334f8eb. An actual deadline still requires
the applicable pay-office calendar, and the calculated date remains
separate from the actual remittance timestamp.

The NT half-pay regression checks full and half payment when one nominal
allowance period spans a rate change. It verifies exact accrued and payable
amounts and retains both condition IDs. All 14 periodic allowance tests
passed on Python 3.15.2. Actual payroll application remains open pending
the Annexure A and conversion evidence in the source-coverage track.

The pinned archive profile maps the leave-loading group at BK1:BP28.
Direct workbook inspection confirmed the raw BK1 label has two trailing
tabs and row 3 uses LL, MP and UL in both units. BL and BO are the
annual and hourly midpoint columns. The separate salary summary at
BK29:BP33 shares the group header. Preserve both regions and the legacy
unmatched result when comparing archived diagnostics.

The workbook profile regression now checks the raw BK1 header and both
midpoint mappings in the detail and summary regions. All six profile
tests passed on Python 3.15.2.

Archive regression also verifies all six lower, midpoint and upper column
meanings and units for both regions. The legacy comparison still reads its
original exact-match groups and retains the delivered diagnostic history.

The focused dynamic qualification passed 37 tests across assignment,
roster, recall and cost properties. Existing cases cover snapshot parity
at constant rates, wage and classification boundaries, elapsed time across
a repeated DST hour, prior-hours overtime and segmentation invariance.
These tests use synthetic releases. Source-backed rule interaction
qualification and the final package gate remain open.

A synthetic overnight roster test crosses the overtime threshold at a wage
boundary. The result is AUD 140 for one ordinary hour at AUD 50 and one
overtime hour at AUD 60 × 1.5. The ledger retains the later salary condition.
All nine roster tests passed on Python 3.15.2.

The levy calendar regression covers a December quarter rolling into the
next year. It excludes the quarter-end date, uses the supplied January
classifications and rejects a calendar missing the twelfth working day.
All 23 period contribution tests passed. Actual deadlines still require
the applicable pay-office calendar.

The levy deadline API now rejects a timestamp supplied as the quarter-end
date before reading the calendar. This prevents timestamp keys from silently
producing a timestamp deadline. All 24 period contribution tests passed.

The archive regression now verifies that the isolated AK39 zero has no
unit, retains the unresolved historical role and stays outside the DSA
aggregate table. Five archive and publication disposition tests passed.

The pinned extraction audit found zero populated nonheader cells without
a declared role. Exactly two cells have an unresolved historical role.
AK39 is the isolated DSA zero and A2 in WS20-R01 is the PSA reference
scalar with unknown unit and estimand. Keep both outside costing inputs
until their original purpose can be verified.

The workbook profile regression now requires a declared name and role for
every populated nonheader cell. All 11 affected tests passed.

Direct inspection of the pinned workbook found that PSA Validation A2
uses General formatting and has no comment or hyperlink. The sheet has
no local defined names, no workbook-scoped name refers to the sheet,
and the workbook has no external workbook links. The scalar remains
an archival comparison value pending the generating calculation, unit
and weighting evidence.

The legacy runner now logs configured archive comparisons skipped for a
missing exact header. It preserves the historical comparison outputs.
Three runner tests passed. Two native projection cases could not complete
because the local LibreOffice conversion exited with status 1.

Hosted main CI at 12c50e5 passed all 999 tests, including all nine legacy
compatibility cases and both workbook projections that failed to start
locally. This verifies the hosted LibreOffice path. The macOS conversion
failure remains open. [Hosted CI receipt](https://github.com/edithatogo/microcosting_healthworkforce/actions/runs/42429103464)

An explicit-calendar regression verifies that a hypothetical additional
weekday closure moves the September 2026 quarter deadline from 19 to
20 October. All 25 contribution tests passed. Actual office closure
classification still requires pay-office evidence.

The v2 CLI accepts `--release RELEASE.json --roster ROSTER.json
--output RESULT.json` for single-worker overtime costing. The roster JSON
contains `period`, `rule`, `activities` and `timezone`. It uses the existing
roster engine and its explicit history and source checks. The synthetic
CLI case yields AUD 125 and retains the rule ID in the output ledger.
All 14 affected CLI and roster tests passed.
