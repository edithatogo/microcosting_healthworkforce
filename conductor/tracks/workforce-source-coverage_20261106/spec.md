# Workforce source coverage and acquisition

Status: specification approved on 6 November 2026. Type: Chore. Registered for implementation. User confirmed the track division and all-sector
coverage, staged public-sector first, on 6 November 2026.

## Overview

Establish a source-backed coverage register for Australian health-workforce
costing, recover the original model's source editions, and acquire missing
instruments in prioritised batches. Cover NSW, VIC, QLD, SA, WA, TAS, ACT, NT and
national instruments, across public, private, not-for-profit, research/academic,
agency and relevant contracted-service settings. Include all workforce groups;
start with public-sector coverage and the five legacy roles.

The [workbook/source audit](../../reviews/workbook-and-source-coverage-20261106.md)
and [physical intake register](../../reviews/workbook-table-register-20261106.json)
are the evidence baseline. The workbook has 20 sheets and 94 physical regions.
Its current 25 priced input rows cover five roles in five states, not the entire
health workforce. All original workbook/configuration bytes remain immutable.

## Functional requirements

1. Define the target denominator before making coverage claims: jurisdiction,
   sector, employer/employer class, profession and occupational subtype,
   classification/grade/pay point, employment basis, instrument family and
   effective period. Maintain a finer occupation crosswalk within broad families:
   medical; nursing/midwifery; allied health; dental; pharmacy; ambulance/paramedic;
   Aboriginal and Torres Strait Islander health; health science/pathology;
   technical/assistant; administrative/managerial; operational/support; and
   research/academic. Agency/on-hire and contracted services are separate
   employment/sector dimensions, not presumed to share employee entitlements.
2. Account for every workbook table and source reference, including metadata
   columns, assumptions, enrolment denominators, weighted/unweighted aggregates,
   alternative headers, component tables, diagnostics and presentation archives.
   Every reference is classified as an award, agreement, variation, wage schedule,
   contract, policy, role description, model assumption or statistical reference.
3. Distinguish `referenced_only`, `held_unverified`, `verified_primary`,
   `verified_applicable`, `superseded`, `unavailable`, `access_restricted`,
   `unresolved_identity`, `conflicting` and `not_applicable_with_reason`.
   A filename, title, portal link or historical transcription is not proof of
   holding, correct jurisdiction, classification, currency or applicability.
4. Reconcile the historic document map and derived VIC transcription without
   promoting them to authority. Correct identifiers with an audit trail:
   Medical Practitioners MA000031, Nurses MA000034, and HPSS MA000027. Resolve
   the blank NSW admin award, ambiguous VIC HPA/MSEBA and WA salaried-officer
   editions, QLD scientist HP versus general-stream attribution, employer-specific
   MCRI applicability, unidentified filenames and state-misfiled national sources.
5. Preserve historical 2022/2023 workbook editions separately from sources current
   at acquisition. Acquire full instruments, schedules, variations, approval or
   commencement evidence and relevant supplementary rules from primary issuers
   or industrial registers. Cross-check employer/industry/occupation coverage;
   record unresolved applicability instead of selecting by job title alone.
6. Record stable source ID, exact title/identifier, issuer, parties/coverage,
   jurisdiction/industrial system, document class, version/variation, source URL,
   retrieval time, file SHA-256, page count/format, source lineage, access and reuse
   terms, approval date, nominal expiry, operative conditions dates, pay-effective
   dates and pay-period/backpay qualifications. Unknown dates remain unknown.
   Nominal expiry must not automatically deactivate an instrument.
7. Stage acquisition: recover legacy references and complete public-sector
   coverage (including missing ACT/NT/TAS and broader professions), then private/
   not-for-profit, research, agency and contracted-service gaps. Prioritise by
   costing use, missing baseline coverage, stale source and contradictory mapping.
   Each batch has explicit scope and pass/blocked dispositions; do not claim a
   census of every employer contract from a sample or a broad profession label.
8. Produce a jurisdiction × profession × sector gap matrix and instrument-level
   backlog, with acquisition route, reason, owner, priority, dependency and
   evidence. Never treat absent sources as zero cost or an award-free occupation.
9. Hand frozen, verified batches to the extraction/costing track using source IDs,
   hashes and applicability decisions. Schema/legacy intake work can proceed
   before nationwide acquisition finishes; authoritative parameter promotion
   waits for the relevant batch, not a blanket assertion of completeness.

## Non-functional requirements

Use repo-local Python 3.15.2, current qualified Polars/Pydantic tooling and ordinary
Git hooks. Keep source documents, workbook-derived values, restricted contracts,
private bindings and receipts outside public source packets. Retain applicable
third-party rights; project Apache-2.0 does not relabel external documents.
Use public official acquisition routes first. Access restrictions are blockers,
not authority for credential transfer, consent workarounds or private document
publication. No email/contact campaign, new subscription or recurring job is
part of this track. Preserve independent GHA/reporting and genomics ownership.

## Acceptance criteria

- All 20 workbook sheets and 94 physical regions have traceable dispositions,
  with semantic subtable splits/typed ingestion handed to the second track.
  No worksheet, empty placeholder or source metadata column is silently dropped.
- All 25 legacy source-row references and all historic candidate-map entries are
  reconciled to held/verified, referenced-only, conflicted or blocked records.
- Every declared jurisdiction/profession/sector cell has an explicit coverage or
  gap status. Coverage percentages name their denominator and accepted evidence.
- Public-sector priority batches and later-sector batches have independently
  reviewable instrument/schedule/variation manifests and applicability evidence.
- No unverified rate or condition is promoted. Every remaining gap has a concrete
  next action or genuine access/source/identity blocker; inaccessible is not done.
- Source-byte integrity, metadata/link checks, duplicate/variation checks and
  extraction handoffs pass. Original inputs and source/native ownership remain
  intact. Scientific assumptions and operational/legal applicability acceptance
  are reported separately from successful acquisition.

## Dependencies and boundaries

This track uses the completed intake audit, not another broad migration review.
The existing modernization plan remains responsible for its independent
performance/reader experiments. The second track consumes verified source batches
and owns extraction schemas/releases and costing interfaces. Neither track may
silently redefine original PSA priors, study weights or cost-method assumptions.

## Out of scope

Automatic legal adjudication; exhaustive discovery of confidential individual
employment contracts; clinical/patient data collection; manuscript claims or
publication; replacing the historical model; treating public portal availability
as permission to redistribute; or marking national coverage complete while
identified source/applicability gaps remain unresolved.
