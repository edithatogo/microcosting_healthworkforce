# Versioned conditions, parameters and static/dynamic microcosting

Status: specification approved on 6 November 2026. Type: Feature. User confirmed static
snapshots plus time-varying activity/roster and effective-dated costing, with PSA
kept separate, on 6 November 2026. Registered for implementation; no completed implementation is claimed.

## Overview

Systematically re-extract all existing workbook/configuration conditions and
parameters, reconcile them against primary instruments as source batches become
available, and create an immutable versioned successor release. Set up the
library for static and dynamic workforce microcosting while preserving the
original model as explicit compatibility mode.

Use the [workbook/source audit](../../reviews/workbook-and-source-coverage-20261106.md)
and [physical intake register](../../reviews/workbook-table-register-20261106.json).
The workbook's 20 sheets, 94 physical regions and all source/assumption metadata
must have typed incorporation or an explicit archival/empty disposition. Reading
only the 25 primary rows is insufficient. Intake must not imply that all tables
are interchangeable accepted inputs.

## Functional requirements: complete extraction

1. Preserve an immutable original edition and raw cell-level lineage: workbook
   hash, sheet, range/cell, header/merged-header context, literal/formula, units,
   cached-value/recalculation status, sheet-local/global names, hyperlinks and
   original display labels. Capture all
   nonempty cells without silently treating absent formula caches as zero.
   Recalculation works on a private copy through the retained qualified route.
2. Build semantic typed tables for primary inputs/source references; Year 0–4
   outputs; ALL/unweighted and WM/Medicare-weighted variants; component dollars
   and shares; Medicare counts/method notes; assumptions; DSA inputs/bounds,
   wide/long values and presentation outputs; fixed-header inputs; and the PSA
   scalar archive. Explicitly represent the empty Labour - BY (%) sheet and
   label-only placeholder blocks. Keep numeric values separate from formatted
   strings and archived interval labels.
3. Reconcile repeated identities, row-order differences, duplicate headers,
   employer/instrument IDs and units. Preserve conflicts and variants instead of
   overwriting them. Specifically handle fixed-header 1.5 versus primary 0.015
   indexation, currency values under percentage-like headers, five-state versus
   eight-state references, workbook Year 0–4 versus library Year 0–5, and DSA
   baseline/axis incompatibility. Keep the 17 false archive diagnostics visible.
4. Re-extract every declared salary/classification/pay-point amount; annual,
   weekly/hourly basis and ordinary hours; employment fractions; superannuation;
   leave and leave loading; overtime/shift/weekend/public-holiday rules; on-call,
   recall, minimum engagements and breaks where sources provide them; attraction/
   retention, private practice, development and other allowances; progression,
   indexation and effective dates. Also record costing-relevant source conditions
   not represented in the old JSON. Unsupported conditions remain explicit gaps.
5. Treat source-derived entitlement, observed quantity/use, analyst assumption,
   statistical weight and uncertainty distribution as different record types.
   Capture calculation basis, additive/compounded/exclusive interactions, caps,
   eligibility, applicability and rounding with clause/page/table citations.
   Distinguish a genuine zero from unknown, missing and not applicable. No
   automatic substitution of legal leave entitlement for observed leave use.
6. Each extracted record carries source ID/hash, instrument version, employer/
   sector/jurisdiction, profession/classification, employment basis, parameter or
   rule ID, typed value/expression, unit/currency, effective interval, approval/
   review state, extraction method, citation, uncertainty and conflict notes.
   Conditions commencement, wage-effective dates, first-full-pay-period rules,
   retrospective backpay and payment date are distinct. Record extraction/review
   time separately from economic effective time; do not backdate knowledge.
7. Release an immutable candidate successor bundle with separate schema version,
   extraction/data release and costing-method version; a manifest, source hashes,
   lineage, explicit missing/conflicted/unreviewed records, change log and complete
   v1-to-v2 diff. Human/source verification is attributable; model output agreement
   alone does not validate extracted entitlements. Only reviewed applicable records
   may enter an accepted costing release. Never overwrite historical priors,
   workbook values or prior release files in place.

## Functional requirements: library interfaces

8. Static microcosting accepts an explicit release/method, as-of/price date,
   jurisdiction/employer/classification and employment basis plus resource
   quantities and units. Return per-resource/component unit costs and totals,
   paid versus productive hours/capacity, currency/price year and source lineage.
   Preserve a rate-snapshot use case and quantity × unit-cost activity costing.
9. Dynamic microcosting accepts dated activity/roster/resource-quantity segments
   and effective-dated wage/condition schedules, rather than equating dynamic with
   PSA or a fixed annual growth multiplier. Split across relevant pay/condition,
   classification/FTE, local calendar and shift boundaries; apply explicit
   overtime/eligibility/interaction rules and chronological carry-over state where
   needed. Require the history needed for cumulative rules. Return an auditable
   event/time/component ledger, totals and the exact rule/source version used.
10. Keep quantities, prices and capacity assumptions separate. Users can hold
    quantities fixed while prices change, change resource mix/rosters, or compare
    paired scenarios. A quantity/capacity change is not automatically a cash saving.
    Preserve nominal-hours baseline; separate productive-hours/leave-cover choices
    without double counting salary, leave cover or paid/unpaid capacity.
11. Use explicit, validated units and pay/rounding conventions. Do not select an
    award from a fuzzy profession string or silently extrapolate an uncovered
    date, overlap conflicting conditions, normalise unknown units, or fill missing
    v2 inputs with legacy defaults. The caller selects an accepted applicable
    bundle; unresolved/overlapping coverage fails with actionable diagnostics.
12. Keep DSA/PSA as optional layers over the same explicit cost function. Original
    seeded compatibility results and original unweighted estimand remain retained.
    New distributions, dependence, weights or tail-precision requirements require
    their own provenance/decision; no clipping or replacement priors is implied.
13. Provide a documented Python library API and bounded CLI access to static and
    dynamic modes with synthetic examples. Preserve existing default CLI/API
    behaviour unless an explicit migration is approved. Do not expose roster or
    staff identifiers, source documents or private research outputs in public tests.

## Verification and acceptance criteria

- All 20 sheets and 94 physical regions reconcile to the raw intake manifest;
  semantic tables have schemas, identities, units, lineage and archive/empty
  statuses. No unknown cached value or failed diagnostic becomes a passing zero.
- Every existing parameter/condition/assumption has a v1-to-successor disposition.
  Every accepted successor value/rule has verified source applicability and
  clause/page evidence; unresolved records stay in the candidate/gap layer.
- Static results reproduce the selected legacy baseline when compatibility mode
  is requested. Any successor-model difference is decomposed into extraction,
  units, instrument date, formula or declared modelling choice, not tuned away.
- Constant-date/rate activity segments reduce to the equivalent static quantity
  calculation. Segmentation/aggregation, proportional quantity scaling, event
  ordering/carry-over, date transitions, employment/classification changes,
  overnight shifts and rule conflicts have targeted synthetic regression and
  property tests. Calendar/holiday data has explicit jurisdiction/version provenance.
- Annual-cost, leave-cover and productive-capacity methods have independent
  arithmetic examples and an explicit cost perspective. No assertion that all
  workforce time is productive or all entitlements are used is hidden in a default.
- Current 100-test baseline and qualified original-workbook/CLI evidence are reused
  where unchanged; changed execution paths receive focused tests, full applicable
  strict/coverage/package gates and new source/installed-CLI parity as warranted.
  Use Python 3.15.2 and existing qualified Polars/Pydantic/Pandera tools.
- Documentation distinguishes static, dynamic, projection, sensitivity and PSA;
  demonstrates release selection, units, failure cases and provenance; and states
  remaining scientific/legal/source acceptance blockers. Installed APIs/CLI run
  outside the checkout. No clinical, legal or operational acceptance is inferred.

## Dependencies and implementation boundaries

The source-coverage track supplies frozen verified batches. Raw/semantic workbook
intake, schemas and immutable compatibility inventory can start immediately;
accepted successor parameter promotion depends on the relevant source batch.
Static costing contracts precede dynamic rule/time integration. The original
modernization track's performance/reader experiments remain separate and must
reuse these contracts rather than start another competing extraction format.
The existing GHA scenario/report owner remains independent; reuse its frozen
receipts without copying private bindings or repeating native workbook mutations.

## Out of scope

A new clinical pathway/discrete-event simulator; patient/staff data ingestion;
authoritative automated legal interpretation; guessed full-sector coverage;
automatic economic-benefit/savings claims; recalibration of original PSA priors;
publication of external source documents or private data; and promotion of an
unreviewed candidate bundle as an accepted costing release.
