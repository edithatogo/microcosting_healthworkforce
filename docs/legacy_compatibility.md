# Explicit legacy compatibility

`src.legacy_compatibility.cost_legacy_compatibility` exposes the existing
formula → annual projection → rate conversion pipeline as an opt-in library
method. Supply `CompatibilityRequest(mode="legacy_compatibility_v1", ...)`,
an already-extracted Polars frame and the legacy formula document. The request
requires the asserted workbook SHA-256, sheet and extraction identity. The
default projection horizon remains five years after year zero; zero selects
only year zero. The original CLI and PSA are unchanged.

The manifest records source assertions, input/configuration/output hashes,
calculation-module identity, runtime versions and selected horizon. Fingerprints
bind original dtypes and scalar string values, distinguish null from NaN, and
preserve column/row order. They exclude unused Arrow storage-buffer bytes. Pins
describe data at calculation time; the returned Polars table remains mutable.
The adapter does not open, recalculate or independently verify a workbook, read
staff data, write outputs, run stochastic analysis or infer effective dates.

Compatibility intentionally retains legacy defaults, missing-column zero
fallbacks, null indexation handling, rate denominators and hourly overrides.
It is not an accepted v2 condition release and does not provide v2 admission
guarantees. Select the condition/unit-quote methods for reviewed source-specific
costing. Legacy workbook assumptions and exploratory PSA qualification remain
distinct from scientific or industrial validation.

Synthetic regression evidence compares the adapter directly with
`WorkforceRun.calculate` and independent annual/hourly arithmetic. Original
workbook compatibility qualification must reuse or perform an explicitly
attributed comparison against the selected workbook/formula edition; a synthetic
match alone does not prove complete workbook parity.
