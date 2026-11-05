# Costing v2 foundation

The v2 modules provide a candidate foundation alongside the existing calculator.
They do not replace the legacy model or constitute an accepted award interpretation.
No real-world condition release is distributed with these modules.

## Workbook intake

`src.workbook_catalog.read_workbook_catalog(path)` preserves worksheet identity,
nonempty cell coordinates, formulas, cached values and their types, formats,
hyperlinks, merged ranges, defined names, and contiguous populated-row regions.
The Polars cell frame carries JSON scalar values and explicit scalar-type tags.
A region is a physical inventory unit, not necessarily a semantic table.
The manifest labels populated worksheets `raw_intake_only`; it is not a claim
that every semantic table or parameter has been incorporated. Formula caches can
be absent. Intake never recalculates or saves the source workbook.

## Source evidence

`src.source_registry` distinguishes source holdings, asserted authority and
asserted applicability. A verified record requires a held-byte hash, retrieval
time, primary-source designation, employer and classification, operative start,
and an exclusive verification horizon. Nominal expiry does not automatically
terminate operation. `verify_bytes` checks a selected file against its hash; the
model does not independently verify that a document is authoritative or applicable.
Reviewers must establish those claims and retain evidence separately.

## Static and dynamic calculations

`src.costing` provides `cost_static` for explicit resource-hours at an instant
and `cost_dynamic` for elapsed activities with an explicit resource quantity.
`flat_hourly_v1` multiplies supplied hourly components by hours. Dynamic intervals
split at effective rate boundaries and use elapsed UTC time; costing fails when
rate or source coverage is absent. A rate is tied to one resource scope, source
hash, citation and declared review. Source dates are interpreted in the rate's
explicit local timezone. Output includes the release, method and component/source
lineage. Decimal amounts are not rounded by the engine.

This method does not interpret awards, infer paid or productive hours, calculate
shift penalties, overtime, leave, escalation or uncertain parameters. Unsupported
required capabilities are rejected. Concurrent activities are additive and must
represent explicit, distinct resource use. A declared review is not legal advice,
independent source verification, or evidence that a rate is scientifically valid.
Condition extraction, rule coverage, release governance, semantic workbook mapping,
and the requested command-line interface remain in the implementation track.

## Table segmentation and condition releases

`src.workbook_tables.extract_tables` applies explicit rectangular definitions to a
workbook catalog, rejects overlapping assignments and unknown sheets, and reports
unassigned cells and empty sheets. A definition may declare column names, units,
roles and header rows. Columns without a reviewed mapping remain unknown; one
physical region may need several definitions, and definitions do not validate the
substantive meaning of archived data by themselves.

`src.source_gaps.screen_gaps` links deliberately scoped discovery leads to
jurisdiction/profession/sector screening targets. It preserves
`applicability_unassessed` whether or not a lead exists; keyword matches and an
empty lead list are neither proof of coverage nor proof an instrument is absent.

`src.conditions.ConditionRelease` stores explicitly reviewed, dated conditions
with source hashes and citations. `annual_salary_components_v1` divides annual
salary and fixed annual components by explicitly supplied annual paid hours, and
applies each specified fraction to salary only. It does not infer which fractions
share a base, derive annual hours from weekly hours, or calculate leave coverage.
`cost_condition_activity` applies those dated conditions to an activity by local
calendar day, using actual elapsed time and retaining condition identities in
each segment. Release citations provide the provenance of each identity. Callers
must resolve the actual effective dates of first-full-pay-period changes; this
method does not derive pay cycles. Source applicability and review are assertions
supplied by the release author, not conclusions independently established by code.
Candidate workbook values cannot be used in an accepted release without review.
