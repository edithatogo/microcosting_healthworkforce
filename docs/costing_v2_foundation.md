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
