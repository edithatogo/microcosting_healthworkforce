# Dapane quotation consumer and namespace migration

The canonical import is now microcosting_healthworkforce. Existing console
command names are retained. The former src imports are explicit compatibility
aliases of canonical modules, preserving class identity and old pickle names.
New callers should use the canonical package, especially when another project
also has a package named src. No employment calculation is changed by the rename.

This provider owns source admission and quotations. Dapane owns valuation and
allocation arithmetic. The adapter exports a bounded, source-selected public
quote and invokes the independently installed native Dapane package. Dapane is
optional; the provider's existing pinned dependencies and Python 3.15.2 requirement
remain unchanged. Genomics consumes the exported JSON in its separately pinned
environment, without importing this provider or relaxing either Python pin.

## Bounded source release

The example in ../examples/dapane/qld-hp3p1-release.json selects the Queensland
Health HP3 pay point 1 published hourly reference of AUD 46.0658, in the table
effective 1 September 2026. The page identifies the hourly column as a reference
value. It is copied directly, without deriving an hourly amount from the
fortnightly or annual columns.

Source: [Queensland Health wage table](https://www.health.qld.gov.au/hrpolicies/wage-rates/health-practitioners#table36083),
last updated 9 October 2026. The complete HTML was obtained and the classification,
pay point, hourly column, effective-date heading and reference-purpose note were
checked. Its SHA-256 is
6948663378e34af05b8dbf91d8799ad1dc14ee831136dc57165d3241d1af17ff.
The full HTML is not redistributed. The release records the public source,
its digest, selected cell, observation and knowledge dates, and interpretation.

Only base_salary is included. Employer superannuation, allowances, casual and
leave loadings, overtime, productive-time conversion and worker classification
decisions are excluded. This is a source-selected reference quote for an explicit
research scenario, not a fully loaded labour rate or payroll eligibility decision.
The example's target laboratory-scientist is an explicit analytic role mapping;
the wage table does not establish the classification of a particular employee.

The quote's exclusive end and source verification horizon are 16 November 2026,
limiting this snapshot to the observation period. This date is not an asserted
legal expiry. Knowledge begins on 15 November 2026. A later observation requires
a new release, source identity check and independent artifact pin.

## Export and consumer API

DapaneQuoteBinding connects one admitted UnitQuote to an explicit target.
Identity-unit bindings use per_quantity 1. The only nonidentity conversion is
source hour to output minute with per_quantity 60. In both cases amount remains
46.0658: no Python division or rounding occurs. Components must exactly retain
the source quote's one component; the adapter rejects inferred loaded components
and renamed synonyms.

The adapter supports source kind published_wage_reference or synthetic only.
The former preserves the provider's held-primary/scoped admission as an observed,
public, source_verified declaration. Synthetic fixtures stay unvalidated.
Neither declaration is empirical validation; Dapane itself does not fetch source
bytes or decide whether a worker is eligible.

Public functions in microcosting_healthworkforce.dapane_adapter:

- export_dapane_quotes(release, bindings) revalidates provider models and returns
  an independent JSON-compatible dictionary.
- load_dapane_quotes_json(text, expected_sha256=pin) verifies an externally selected
  pin and regenerates every quote from the complete source snapshot and bindings.
- build_dapane_request(text, quantities, expected_sha256=pin, run_id=...,
  knowledge_cutoff=date(...)) constructs a core 0.1 request. Quantities are existing
  QuoteQuantity models whose quote_id identifies an exported quote.
- evaluate_dapane(...) has the same arguments and delegates the request to
  installed dapane.evaluate. There is no fallback Python valuation formula.

For the example, output IDs are qld-hp3p1-hour-20260901 and
qld-hp3p1-minute-20260901. The complete release, bindings, resulting artifact and
independent pin are adjacent JSON/text files under examples/dapane.

## Artifact contract: workforce-dapane-quotes/1

The envelope contains schema_version, provider, release_id, as_known_on,
release_snapshot, release_sha256, bindings, quotes and artifact_sha256.
The complete provider release snapshot includes each source record and original
quote. The bindings retain explicit unit/component interpretation and price year.

Canonical serialization is UTF-8 JSON with sort_keys=True, ensure_ascii=False,
separators=(",", ":"), and allow_nan=False. release_sha256 hashes the complete
release_snapshot. artifact_sha256 hashes the entire envelope except its own field.
These are lowercase hexadecimal SHA-256 values without a prefix. Dapane source
content_digest retains the separate original source byte digest with sha256: prefix.

The parser rejects duplicate object keys at every level, floating and nonfinite
numeric tokens, unknown or substituted envelope fields, missing pins, inconsistent
source/quote projections, excessive nesting and payloads above 2 MB. Price year is
a strict integer. Amounts and quantities never traverse binary floating point.
Before fixed-point or rational string conversion, transport enforces Dapane's
96-digit numeric and 36-place decimal-scale limits. Compact huge exponents cannot
expand into unbounded strings.
A new internally consistent hash alone does not authorize a source: callers pin
the chosen release independently.

The new canonical release hash is deliberately distinct from legacy price_units'
unchanged hash of release.model_dump_json(). Do not compare these hash schemes
as if they were the same identity contract. Preserve the method and algorithm
beside each pin.

## Compatibility, comparison and rollback

Existing price_units, condition costing, workbook compatibility and console
commands remain explicit alternatives. Select the old engine by calling it
directly, or reinstall the previous qualified provider revision. The Dapane path
never silently replaces a historical engine or changes a stored result.

A one-hour public reference exposure is exactly 230329/5000 AUD. A one-third
minute exposure is exactly 230329/900000 AUD; half-even line rounding at two
decimal places yields 0.26. The dated workforce and genomic examples use the
same Rust implementation. These resource quantities are synthetic acceptance
inputs, not measured laboratory staffing.

Historical workbook comparisons keep mechanical extraction, expected method
differences and source-specific repairs separate. Legacy rate denominators,
missing-column behavior, workbook source assertions and original output artifacts
remain under their existing contracts. Namespace-induced engine-file fingerprints
change; numerical history must not be relabelled as a new source edition.

## Verification status

The pinned Python 3.15.2 environment and original locked dependencies installed
successfully before the local execution environment became unavailable. Hosted
CI and the Dapane coordinating track provide subsequent exact-head runtime and
independently installed two-consumer evidence. Initial implementation commits do
not establish passed checks or complete the broader workforce research tracks.
