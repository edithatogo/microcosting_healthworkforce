# Static snapshots and dated unit-quote events

`microcosting-healthworkforce-units` exposes the existing
`src.unit_quotes.price_units` calculator using JSON files. It requires an explicit
accepted `UnitQuoteRelease`, a request with an explicit mode and a new output path.
It does not select a source, infer eligibility, convert pay units or calculate
wages from a roster. The default workforce command and the condition-based v2
command retain their existing behavior.

## Runnable synthetic examples

The three files in `examples/unit_quotes/` are fictional contract fixtures.
Their source URL, hash, review/applicability labels, wage amounts and employment
scope are synthetic. They demonstrate schema and arithmetic, not a held instrument
or real employee entitlement. Keep real instruments and staff data private.

After installing the project with its locked Python 3.15.2 environment:

```sh
uv run --locked microcosting-healthworkforce-units \
  --release examples/unit_quotes/release.json \
  --request examples/unit_quotes/snapshot.json --output /tmp/unit-snapshot.json

uv run --locked microcosting-healthworkforce-units \
  --release examples/unit_quotes/release.json \
  --request examples/unit_quotes/events.json --output /tmp/unit-events.json
```

Choose unused output paths. The snapshot explicitly prices one fortnight at
100.01 for development and one independently quoted registration annum at 2700: exact total `280001/100`
(2800.01 AUD). It does not equate an annum with 26 fortnights. The event example
prices one selected fortnight quantity on 30 June at 100.01 and one on 1 July
at 110.01: exact total `10501/50` (210.02 AUD). These are supplied quantities
at valuation dates, not a declaration that either date is a payroll boundary.

`python -m src.unit_quotes_cli` accepts the same flags when the installed entry
point is unavailable during development. The Python API remains `price_units`;
the CLI calls that same function and adds request/mode provenance.

## Request and release dictionaries

A snapshot request has `mode: "snapshot"`, an ISO `as_of` date and a nonempty
`quantities` array. Every `valued_on` must equal `as_of`. An event request has
`mode: "events"` and a nonempty `quantities` array with individually selected
dates; it rejects `as_of` rather than treating multiple dates as one snapshot.
Input order is retained. No stateful temporal rule is implied by that order.

Every quantity requires `quantity_id`, `quote_id`, `unit`, `quantity`, `valued_on`,
`quantity_kind` and `basis`. Quantities are finite nonnegative decimal strings
or exact fractions such as `"1/3"`. Provenance is `observed_use` or
`analyst_assumption`; a supplied label is not independent verification.
A known zero still produces a ledger row. Missing/empty inputs are rejected.

A release requires its identity/method, currency, knowledge date, jurisdiction,
employer/classification scope, source registry and accepted dated quotes. Every
quote names its source/hash/citation, denominator unit, amount, effective interval
and evidence knowledge date. Source, status, units, date bounds and duplicate
quantity/quote checks are the library's existing checks. A schema-valid accepted
label cannot establish real-world source authority or individual applicability.

## Output and exact arithmetic

The output envelope carries `schema_version: 1`, explicit `mode`, snapshot
`as_of` (null for events), `request_sha256` of the exact request-file bytes and
`result`. The shared result retains the release identity and normalized release
hash, method, currency, knowledge date, each original quantity and selected quote,
source hashes/citations, exact row costs and total. Fractions are JSON strings;
use `Fraction(value)` when consuming a rational total. Do not parse them as floats
or infer a currency-rounding or cents-allocation policy.

The request-byte hash changes with file formatting; the release hash represents
the library's normalized model serialization. Retain original inputs with the
output for reproducibility. Validation and serialization finish before exclusive
output creation. Existing output/input aliases are never overwritten. Invalid
mode, date, units, duplicate quantities or unqualified release inputs fail before
a result is created.

## Choosing the appropriate interface

Use the original `microcosting-healthworkforce` command for legacy workbook
compatibility, DSA and explicitly exploratory PSA. Use
`microcosting-healthworkforce-v2 --release ... --snapshot ...` for explicit
condition-based paid hours at a date, or `--activity ... --timezone ...` for a
timed activity split at effective condition/local-day boundaries.

Use the unit command for already selected, unit-matched quantities at explicit
valuation dates. It does not allocate a quantity spanning a price change, derive
resource hours from timestamps, apply overtime/recall/leave rules, select component
inclusions or combine ledgers automatically. A timed roster or stateful rule must
first be evaluated by the relevant supported library method with complete history.
Review duplicate economic costs, allowance inclusion and paid/productive capacity
before combining outputs. PSA remains a separate uncertainty layer.

See [the library guide](costing_v2_foundation.md),
[leave pricing](leave_pricing.md) and
[whole-window annualised comparisons](annualised_pay.md) for the supported
calculation boundaries. National source coverage, actual worker applicability,
unknown workbook meanings and scientific PSA validation remain separate gaps.
