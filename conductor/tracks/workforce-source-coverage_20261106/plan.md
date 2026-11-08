# Workforce source coverage and acquisition — implementation plan

Status: in progress. The approved plan has a source-registry foundation and a first
official-source discovery batch; source applicability and jurisdictional coverage
remain unqualified. See the implementation receipt below.






## Tasmanian public-sector discovery — 6 November 2026

The [Tasmanian discovery review](../../reviews/tas-public-source-discovery-20261106.md) identifies later allied-health, ambulance, nursing and rural-medical leads and a documented distinction between ambulance decision and commencement dates. Direct decision downloads returned HTTP 403; source bytes, scope, variations and actual worker applicability remain unverified.

## ACT public-sector source batch — 6 November 2026

The [historical ACT batch](../../reviews/act-historical-source-batch-20261106.md)
adds six held, hash-verified previous agreements and records original operation,
nominal expiry and the medical variation separately. The nursing document's
title differs from the portal label. A medical outreach allowance arithmetic
discrepancy has a plausible two-increase explanation in the earlier and later
agreements, but its starting amount and payroll timing remain unverified, as do
worker applicability, further variations and rights.
The private 576-row successor now separately links the seven historical ACT
editions to ten public-sector profession-family targets (eleven candidate
links). Coverage clauses, source hashes and target identities were checked;
all such links remain unassessed for individual applicability.
A further successor adds the earlier medical agreement: 12 historical candidate
links to eight hash-verified editions, with all 576 targets retained.

The [ACT batch review](../../reviews/act-public-sector-source-batch-20261106.md) records six retrieved and hash-verified primary source files with separate candidate SourceRecords. The medical file is a determination with a retrospective variation. The batch review now traces each instrument’s coverage clause and classification schedule, including historical employer wording. Seven held ACT candidates are linked to ten ACT/public screening targets in a versioned 576-row private register; links remain applicability-unassessed. Worker-specific scope, later changes, rights and accepted conditions remain unresolved.

The nursing edition's 6 August 2024 approval and seven-day commencement clause
give an original operative date of 13 August 2024, recorded in a separate private
candidate successor. This does not resolve pay-effective dates, later variations
or worker applicability.

## ACT health-professional source — 6 November 2026

The [ACT source review](../../reviews/act-health-professionals-source-20261106.md)
now records a strong arithmetic explanation for the professional-lead table:
the 2022 HP5.2–HP4.2 gap, indexed by the later table's seven percentage factors,
reproduces all five published level-3 amounts when rounded. The earlier official
agreement and arithmetic receipt are retained privately. Intent, classification
transition, payroll timing and worker eligibility remain unresolved; this is
not an accepted industrial interpretation.

The [ACT source review](../../reviews/act-health-professionals-source-20261106.md) records a hash-verified official agreement edition, scoped candidate coverage, position-specific weekly hours and a retrospective 2026 correction. A private 32-record successor preserves the previous 17 candidates and adds dated professional-lead table amounts and calculation lineage. The percentages use a separately calculated allowance, not salary; displayed amounts differ from direct percentage arithmetic by up to $0.60 per annum. A separate comparison found that obvious Annex A pay-point differences do not reproduce the Annex C level-3 figure; commencement, payroll and classification-transition basis remain unresolved. Employer/position eligibility, rights and later variations remain unverified; no condition was accepted.

## Northern Territory public-sector discovery — 6 November 2026

The [NT discovery review](../../reviews/nt-public-source-discovery-20261106.md) identifies five official instrument leads and selected approval/operation/nominal-expiry evidence. The selected direct agreement downloads returned HTTP 403, so source bytes, full coverage, variations and individual applicability remain unverified; no NT rates were accepted.

## Queensland applicability cross-check — 6 November 2026

The [historical instrument comparison](../../reviews/qld-workbook-applicability-20261106.md) distinguishes indicative occupational groupings from agreement coverage and the different award relationship for clinical assistants. It identifies the employer, appointment, stream and date evidence needed to resolve the conflicting workbook classification. A separately retrieved 1 September 2022 HPDO award expressly lists medical laboratory scientists and technicians and specifies a 38-hour average ordinary week for covered employees; the workbook uses 36.25 for those two roles. Coverage and denominator intent remain unverified. The later HP agreement also lists these disciplines; the general award's 36.25-hour pathology provision has specific employment and continuity conditions. Four workbook rows use 36.25 hours; a 38-hour comparison changes their hourly denominator by about 4.83%, holding annual cost fixed. No individual entitlement is inferred.

## South Australian historical salary reconciliation — 6 November 2026

The [SA source comparison](../../reviews/sa-2022-workbook-source-reconciliation-20261106.md)
visually checks four scanned salaried-agreement schedules and separately the
medical-scientist award minimum. Workbook endpoints are close but not identical;
two upper labels differ from the selected close classifications. Applicability,
source intent and individual applicability remain unresolved. The dated 2022 medical-officer schedules were visually compared; their salary-sacrifice schemes differ and neither matches the workbook endpoints exactly. A 2022-named AGD URL delivered a 2025-labelled document and is not used as 2022 evidence.

## Comparative costing templates — 6 November 2026

A historical NSW workbook and its first-pass migration inventory, plus two
Queensland project-attached labour costing workbook copies, were located in
restricted sources. The Queensland 2026 copy includes pay progression,
allowances, leave backfill, overtime, penalties and on-cost sheets. Source
identities and byte hashes are retained in the ignored private evidence area;
these copies are comparative evidence, not current or universally applicable
authority. Establish provenance, redistribution rights, effective dates and
applicable awards before extracting or accepting any rates or rules.

## Queensland EB11 salary reconciliation — 6 November 2026

The [EB11 source trace](../../reviews/qld-eb11-workbook-reconciliation-20261106.md)
links Queensland laboratory and administrative endpoints to the certified
agreement's 1 September 2022 schedules. Identical laboratory amounts occur in
multiple streams; worker scope and the 2023 certification/2022 wage-date
distinction remain explicit. Practitioner-row amounts match General Employees professional Level 2–6 reference salaries, while the HP2–HP3 label belongs to a different health-practitioner scale; worker applicability remains unresolved. The Queensland medical-officer upper workbook endpoint matches L29 in a 2023 reprint, while its grade label ends at L27; dates and individual applicability remain separate.

## NSW historical salary reconciliation — 6 November 2026

The [NSW 2022 review](../../reviews/nsw-2022-workbook-source-reconciliation-20261106.md)
records recovery of the previously unavailable official gazette and matches
both endpoints for the laboratory and scientist workbook rows to specific
salary tables. Individual classifications, employer and pay-period applicability
remain unresolved; the historical matches are not accepted entitlements. A further bioinformatics candidate matches a restricted transferred-staff table across different 2021/2022 rate columns; its source and applicability remain unresolved. Administration endpoints also match different pay-period columns in a 2022 award; the staff-specialist upper amount matches Senior rather than the labelled level 5. These are candidate matches, not individual applicability. A 2022 Hospital Scientists clause supports a 38-hour average for its ordinary-hours measures; the workbook bioinformatics row records 40, with basis and coverage unresolved. Technical and administrative candidates also have 40-hour inputs versus a conditional 38-hour roster average under their incorporated 2022 conditions award; individual roster basis remains unresolved.

## Source integration — 6 November 2026

Source foundation and costing commits through `073c3d3` were integrated by
[PR #46](https://github.com/edithatogo/microcosting_healthworkforce/pull/46),
merged as `5e82c56`. Exact-head checks and receiving-main CI and Security passed;
local `make ci` passed 142 tests on Python 3.15.2. The integrator reconciled the
lane-freeze checklist against the existing manifest, runtime and ownership
receipts. The bounded register exists; complete inventory import, source
applicability and all declared jurisdiction/sector coverage remain open.

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
extraction, historical NSW acquisition timeout and source commits `30da372` and
`f9fdb44` for overtime and paid-capacity scenarios. Full `make ci` passed with
127 tests on Python 3.15.2. One isolated workbook cell is explicitly unresolved and broader
semantic, applicability and costing-rule qualification remains open. Neither
track is complete and no accepted national condition bundle is implied.

## Continuation receipt — 6 November 2026

Source commit `87d08a7` adds explicit table segmentation, candidate condition
releases, limited annual-salary rules, dated activity costing and scoped source
gap screening. The full repository `make ci` passed on Python 3.15.2 with 120
tests. The private [implementation review](../../reviews/workforce-v2-implementation-20261106.md)
records extraction reconciliation, the initial NSW instrument batch, remaining
semantic/source gaps and boundaries. Both tracks remain in progress; raw or
keyword discovery coverage is not reviewed economic or industrial coverage.

## Implementation receipt — 6 November 2026

Source foundation commit `3622856` in the isolated `codex/workforce-costing-v2`
worktree distinguishes holding, declared authority, scoped applicability, hash,
operative dates and an exclusive verification horizon. Focused synthetic tests
and the complete `make ci` gate passed on Python 3.15.2 (111 tests). This is
not yet the full planned gap-register import or applicability review.

The GHA owner’s frozen 11-record manifest was checked once: all eight saved
artifacts match their recorded hashes; three previously unavailable requests
remain unavailable. Their rights and applicability remain unresolved. A new
private discovery batch retained six state/territory index pages and three
national award pages; four requests returned HTTP 403 (two Queensland, one
Tasmania and one Northern Territory). Receipt and byte hashes are at
`.private-runs/workforce-source-coverage-20261106/manifest.json`; a successful
response does not establish instrument coverage, currency, rights or scope.

## Frozen starting evidence and ownership

- Read the [approved specification](./spec.md) and canonical
  [workflow](../../workflow.md).
- Reuse the 20-sheet/94-region intake, 69 historic candidate entries, 25 legacy
  source rows and 576-cell initial screening matrix. The latter is not an
  exhaustive employer/occupation census or a count of required instruments.
- Qualified source main: 11df8b3; original workbook SHA-256 is pinned in the intake
  register. Preserve original input/configuration bytes and every prior edition.
- The GHA owner reports edition 22/source 3bb926e with eight locally retained public
  sources and three preserved HTTP 403 failures. This is an external owner handoff,
  not eight sources already held/accepted in this repository. Verify its frozen
  manifest, rights and hashes once before registering reusable evidence; do not
  repeat acquisition or copy private DVC/authentication bindings as discovery.
- This chat remains integrator for main, Conductor and dependencies. Source
  implementation uses a separate, verified clean worktree based on current main;
  acquisition artifacts stay in an explicitly owned private evidence location.
  GHA reporting/scenarios and genomics retain their existing owners.

## Phase 0: Reconcile baseline, scope and reusable evidence

- [x] Task: Freeze the actual implementation and acquisition lanes.
  - [x] Inspect worktrees, branch/dirty state, active operations and current path
    ownership; record exact chat/worktree/source scope before any writes.
  - [x] Pin source/runtime/configuration/workbook and the inherited audit hashes;
    verify the actual repo-local Python 3.15.2 interpreter.
  - [x] Read the GHA edition-22 source manifest and identify reusable public
    sources/failed requests; preserve evidence attribution and private ownership.
- [ ] Task: Enumerate the target coverage denominator.
  - [ ] Expand broad families into occupational subtypes, employers/employer
    classes, grades/pay points and employment bases; retain an explicit unknown
    category where scope is not yet enumerated.
  - [ ] Separate eight jurisdictions, national industrial systems and six sector
    dimensions; document overlaps without double counting accepted coverage.
  - [ ] Define batch target IDs and priority: historical recovery and public
    sector first, then remaining sectors. No unattested completion percentages.
- [ ] Task: Phase Verification & Checkpoint (refer to ../../workflow.md).
  - [ ] Manually inspect scope, source hashes, exclusions and reusable receipts;
    record unresolved ownership/identity/access questions without starting a
    competing source or native operation.

## Victorian scientist reconciliation — 6 November 2026

The [source reconciliation](../../reviews/victorian-scientist-source-reconciliation-20261106.md)
traces the workbook's 2017–2021 source note and historical salary endpoints to a
retained VHIA circular. They support RX1–RZ7 while the workbook grade label says
RX4–RZ7; author intent, employer and actual applicability remain unresolved.

## Phase 1: Executable source and gap registers

- [ ] Task: Write focused failing register-contract tests before implementation.
  - [ ] Cover stable identity, duplicate/variation relationships, missing title/
    source bytes, pattern-only references and conflicting identifiers.
  - [ ] Cover holding, authority and applicability as separate axes; a successful
    download must not automatically become verified applicability.
  - [ ] Cover date provenance, unknown dates, nominal expiry versus continuing
    operation, retrieval hash changes and auditable status transitions.
- [~] Task: Implement the bounded register and validation interface.
  - [ ] Use existing Pydantic/Polars contracts and portable JSON/tabular manifests;
    do not introduce a database/cloud framework or duplicate extraction schemas.
  - [ ] Preserve original map labels and code corrections with exact source
    citations, and import the legacy-row/region inventory losslessly.
  - [ ] Add owner/priority/next-action/dependency fields and explicit failed,
    restricted, unknown, conflicted and reasoned-not-applicable dispositions.
- [~] Task: Verify register integrity and gap reports.
  - [ ] Account for all 69 historical entries and 25 source-row references;
    patterns/ranges remain patterns until actual files are enumerated.
  - [ ] Verify jurisdiction/profession/sector totals and drill-down to instrument
    chains without counting the same instrument repeatedly as new acquisition.
- [ ] Task: Phase Verification & Checkpoint (refer to ../../workflow.md).
  - [ ] Review exact affected tests and inspect sample accepted/rejected records;
    record full-gate evidence at the coherent source-code milestone.

## Phase 2: Historical source recovery and five-state public baseline

- [ ] Task: Recover the original instrument editions and supporting schedules.
  - [ ] Resolve VIC HPA/MSEBA, grade/reference conflicts and employer-specific
    MCRI bioinformatics applicability; preserve historical/current editions.
  - [ ] Resolve SA technical/ASO/PO/scientist/medical sources without treating an
    email or costing workbook as a legal pay instrument.
  - [ ] Resolve NSW administration's blank award and the technician/scientist/
    specialist classification and determination chains.
  - [ ] Resolve QLD HP versus general-employees attribution, pay streams and
    medical grades; do not extend category-specific allowances to generic roles.
  - [ ] Resolve WA salaried-officer editions/grades, PACTS/HSU and medical
    agreements, arrangements and supplementary rules.
- [ ] Task: Qualify each source chain and exact applicable scope.
  - [ ] Retrieve primary instruments, approval/commencement evidence, variations
    and wage schedules through supported official routes; retain byte hashes,
    retrieval/access history, terms and source lineage privately.
  - [ ] Resolve national award identifier reversals and state-misfiled entries;
    preserve old labels rather than rewriting historical evidence.
  - [ ] Record instrument-specific eligibility. Inherited GHA QLD allowance and
    WA Arrangement A evidence cannot be treated as universal role entitlements.
  - [ ] Hand the first frozen verified batch to the extraction track; retain
    unresolved items as explicit gaps and do not wait for nationwide completion
    before delivering a genuinely qualified subset.
- [ ] Task: Phase Verification & Checkpoint (refer to ../../workflow.md).
  - [ ] Inspect document identity/pages and sampled cited clauses; verify hashes,
    applicability evidence and historical/current separation, not merely URLs.

## Phase 3: Missing jurisdictions and broader public-sector workforce

- [ ] Task: Acquire ACT, NT and TAS public-sector instrument chains.
  - [ ] Include health/medical/nursing and general professional/technical/support
    streams, with employer and classification mappings.
  - [ ] Distinguish agreement approval, conditions commencement, wage-effective
    and first-full-pay-period dates, including retrospective pay/backpay evidence.
- [ ] Task: Fill profession and employment-basis gaps across all eight jurisdictions.
  - [ ] Cover nursing/midwifery, allied health, dental/pharmacy, ambulance/paramedic,
    Aboriginal and Torres Strait Islander health, science/technical/assistant,
    administrative/managerial, operational/support and research-related roles.
  - [ ] Enumerate actual occupational/classification targets within families and
    identify separate awards, agreements, policies and wage schedules as needed.
  - [ ] Record permanent/part-time/casual, trainee, executive, on-call/visiting and
    other relevant employment bases; do not imply every cell is applicable.
- [ ] Task: Deliver verified public-sector batches with remaining-gap receipts.
  - [ ] Reconcile all declared public targets to verified coverage, reasoned
    exclusion or a genuine unresolved gap; keep unresolved tasks open.
- [ ] Task: Phase Verification & Checkpoint (refer to ../../workflow.md).
  - [ ] Review each jurisdiction/family scope and frozen extraction handoff;
    report source availability separately from costing-model acceptance.

## Phase 4: Private, not-for-profit, research, agency and contracted services

- [ ] Task: Enumerate employer/industry-specific coverage and source routes.
  - [ ] Identify relevant national awards, enterprise agreements, employer
    schedules and appropriately authorised contract templates, rather than
    assigning one public instrument to an entire private profession.
  - [ ] Separate employee entitlements from agency charging/service fees and
    contracted-service terms; record relevant tax/on-cost questions as gaps.
- [ ] Task: Acquire and verify later-sector batches.
  - [ ] Preserve access/reuse restrictions; do not solicit confidential individual
    contracts, send messages or acquire new permissions/subscriptions by default.
  - [ ] Reconcile employer/occupation/industrial-system applicability and dated
    variations; retain unavailable or restricted records without inventing values.
  - [ ] Hand each qualified subset to extraction with immutable source identity.
- [ ] Task: Phase Verification & Checkpoint (refer to ../../workflow.md).
  - [ ] Inspect source rights, applicability, gaps and unchanged private bindings;
    retain an honest batch/track status if the declared scope remains incomplete.

## Phase 5: Coverage release, documentation and terminal handoff

- [ ] Task: Produce a versioned coverage release and source-to-extraction handoff.
  - [ ] Freeze register/schema/manifest versions, applicability decisions, source
    hashes, duplicate/supersession edges and all unresolved-target dispositions.
  - [ ] Publish only approved source-code/metadata documentation; source PDFs,
    restricted contracts, values and private evidence remain outside public packets.
  - [ ] Update workbook/source documentation, matrix definitions and reproducible
    acquisition/recovery instructions; no automatic recurring acquisition job.
- [ ] Task: Run applicable final qualification and source integration.
  - [ ] Validate register/link/hash consistency and focused/full code gates, inspect
    package contents where changed, and reuse unchanged workbook/native receipts.
  - [ ] Use integration preflight, whole outgoing-range privacy scans and exact-head
    Actions before any authorised merge; verify receiving main before pruning.
  - [ ] Record the next owner/action for every unresolved source or applicability
    gap; track completion requires the approved target scope actually be resolved.
- [ ] Task: Phase Verification & Checkpoint (refer to ../../workflow.md).
  - [ ] Supply one terminal evidence handoff with exact revision, covered denominator,
    source batches, tests, remaining blockers and private artifact locations.

## Cross-track dependencies and stop conditions

The extraction track can start raw workbook/schema work immediately. Accepted
successor parameters depend on the relevant verified source batch. Acquisition
does not approve scientific assumptions, and output parity does not verify source
applicability. A malformed response, login/interstitial, changed document hash,
missing schedule or ambiguous employer/classification is a scoped stop for that
record, not permission to bypass access controls or declare the whole batch valid.
No native workbook replay or original-parameter recalibration is required merely
to complete acquisition. Current scientific PSA blockers remain independent.

## Skill review

The installed Conductor catalog was reviewed. Its missing Firebase/GCP deployment
skills do not match this Python/source-acquisition scope. No new skill installation
or environment refresh is needed. Use existing document-reading skills when an
actual PDF/workbook extraction step begins.

## Storage interruption — 6 November 2026

Continuation was interrupted by ENOSPC while creating a rule-interaction module; pytest could not create temporary files. The incomplete untracked test was removed and no new source change or passing validation is claimed. Both data volumes remain nearly full. See [ownership](../../ownership.md) for the exact recovery boundary. Recheck writable free space before resuming.

## Additional budgeting sources — 6 November 2026

NSW and Queensland budget workbooks were located and structurally inspected as
restricted comparison sources. They do not close award or applicability gaps;
see [template discovery](../../reviews/workforce-budget-template-discovery-20261106.md).

## Held-source candidate linking — 6 November 2026

Isolated branch `codex/workforce-source-linkage`, commit `df9dcd3`, adds
validated, reasoned associations between held source editions and existing gap
targets without changing their unassessed status. Eight focused tests and Ruff
passed; focused basedpyright reported no errors on Python 3.15.2. A private run
reproduced the 576-target ACT-linked register, validated 11 links across ten
targets, and verified the hashes of all seven held source editions. The receipt
is `gap-candidate-link-validation-v1.json` alongside the private register.
Occupation, sector, employer and effective-date applicability remain separate
decisions. Outgoing Gitleaks and reviewed Presidio passed; [PR #66](https://github.com/edithatogo/microcosting_healthworkforce/pull/66)
is open with hosted checks and integration pending.

## NT and Tasmania acquisition checkpoint

The [held-source review](../../reviews/nt-tas-held-source-batch-20261107.md)
supersedes the download-failure disposition for the selected 28 PDFs.
Source holdings and candidate transcriptions are evidenced. The separate
[ACT acquisition review](../../reviews/act-public-sector-source-batch-20261106.md)
records six verified files and seven held candidates linked to ten public-sector
screening targets, including the separately acquired health-professionals
agreement. The retained nursing edition commenced on 13 August 2024.
Later variations, complete instrument chains, employer and classification
coverage, and the applicable pay period remain open.

## NT professional-health applicability checkpoint

The [professional-health source review](../../reviews/nt-professional-health-chain-20261107.md)
records candidate scope for three NT public-sector cohorts and separates
market allowance, retention and receipt-based exclusions. Approval
undertakings and operative, transition and end dates are documented.
Actual worker cohort and service history, missing instrument links and
payroll treatment remain open.

## NSW source chain reviews

The retained reviews qualify selected source chains and distinguish
candidate rates from worker-level applicability.

- [Crib-away rate chain](../../reviews/nsw-crib-away-rate-chain-20261107.md)
- [Dental source chain](../../reviews/nsw-dental-source-chain-20261107.md)
- [Hospital science chain](../../reviews/nsw-hospital-science-chain-20261107.md)
- [PTO parent chain](../../reviews/nsw-pto-parent-chain-20261107.md)
- [Skilled trades chain](../../reviews/nsw-skilled-trades-chain-20261107.md)

## Nursing, retention and delegate award evidence

- [Public nursing source chain](../../reviews/public-nursing-source-chain-20261107.md)
  records at least one held candidate for each of the eight public nursing and
  midwifery screening rows.
- [Nursing dependencies](../../reviews/nursing-dependency-chain-20261107.md)
  records subsequent source acquisitions and operative-text corrections.
- [Retention source boundary](../../reviews/retention-source-boundary-20261107.md)
  records conditional source-price parity for the NTPS retention allowance.
- [NT delegate award dependency](../../reviews/nt-delegate-award-dependency-20261107.md)
  records acquisition of the award referenced by the approval undertaking.

The review counts describe their respective matrix versions. Worker coverage,
eligibility and payroll evidence remain separate acceptance requirements.

## Queensland health practitioner and dental officer chain

The [current HPDO source review](../../reviews/qld-hpdo-current-chain-20261107.md)
and its [development policy companion](../../reviews/qld-hpdo-development-interaction-20261106.md)
record instrument and policy dependencies, dated rate comparisons and
qualification boundaries. Individual eligibility and application approvals
remain separate from the documented source chain.

## Vehicle and exemplary practice source checkpoint

For Queensland medical officer vehicle allowances, MOCA7 clause 11.33
supports a recurring payroll remuneration classification. The WorkCover
wages manual distinguishes remuneration from reimbursement. Confirm the
employer premium scope, eligible gross salary mapping for the Treasury
long-service leave levy and the applicable Commonwealth and Queensland
superannuation bases before approving a release.

For NT Aboriginal health practitioners, the Fair Work Commission register
establishes the 31 March 2026 agreement operation date. Schedule D and
clause 46 establish the fixed classification reference and payment
conditions. PR #225 verifies the generic dated quote arithmetic with
synthetic amounts. The [published approval decision and agreement](https://ocpe.nt.gov.au/__data/assets/pdf_file/0008/1604663/northern-territory-public-sector-aboriginal-health-practitioner-2025-2029-enterprise-agreement.PDF)
identify the undertaking as a term of the agreement and locate it at
Annexure A on PDF page 3. The searchable text shows only the annexure
heading, so applicability review still requires a legible page image or
transcription. Match any replacement copy against FWC agreement AE532390,
approval [2026] FWCA 749 and matter AG2026/305 before checking whether the
undertaking modifies clause 46 or clause 80.19. The official download routes
returned HTTP 403 from the CLI and the local filename search found no copy.
Actual payroll conversion remains a separate evidence gap.
Clause 80.19(d) governs the extended half-pay period and leave accrual.
Clause 80.19(h) separately limits counted service to the full-pay equivalent.
Keep these quantities separate from the monetary allowance calculation.

## Candidate workforce weighting sources

The [2021 Census occupation dictionary](https://www.abs.gov.au/census/guide-census-data/census-dictionary/2021/variables-topic/income-and-work/occupation-occp)
uses ANZSCO 2013 v1.3. Candidate matches for three workbook roles are
Medical Laboratory Scientist (234611), Medical Laboratory Technician
(311213) and Pathologist (253915). Administrative and bioinformatics
staff still need service-specific role definitions.

Cross-tabulate by workplace state or territory and main-job industry.
Compare all-industry counts with separate hospital (8401) and pathology
and diagnostic imaging (8520) strata. Retain unknown and imputed
workplace geography separately. These industry codes do not identify
hospital laboratory departments or isolate pathology from imaging.

The pathology workforce review provides a senior-scientist FTE
benchmark. Its Fellow counts describe a narrower population in
headcount. An accepted replacement series still requires a matched
extract, a common denominator and coverage of all five roles.

The public Working Population Profile uses broader occupation groups.
The September 2026 ABS data-item list identifies TableBuilder Basic
Employment, Income & Education as the route for six-digit occupation,
industry, workplace geography and the workplace imputation flag. Basic
provides hours bands. Pro lists a separate hours worked field. A native
export must still verify industry class selection and suppression before
these data can support replacement weights.

Source screening now rejects whitespace-only lead identities, titles and
locators. Five focused screening tests passed. Lead validation preserves
the distinction between discovery and assessed applicability.

Appendix A of the [Queensland Treasury scheme guidelines](https://www.treasury.qld.gov.au/files/Long-Service-Leave-Central-Scheme-Guidelines-2.pdf)
confirms one remittance per agency or pay-office code per quarter and
requires the remittance information at least one day before the EFT.
The twelfth working day is the receipt deadline. Keep the information
submission, actual EFT and calculated receipt deadline separate. Appendix A
does not specify which local holidays or office closures count as working
days, so retain the applicable pay-office calendar as an explicit input.
