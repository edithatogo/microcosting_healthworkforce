# Count-band quoted allowances

`src.count_bands.price_count_bands(rule, release, cases)` selects an explicit
integer-count band and prices independently allocated quantities with the shared
`price_units` engine. One case is a static valuation; a sequence of dated cases
is an explicit dynamic scenario. The function does not derive a headcount, worker
eligibility, hours-to-weeks conversion or accrual from an activity duration.

For fictional prices10/week in a small band and22/week in a later medium band,
one explicitly allocated week in each costs32. It does not select the largest
available price. Three independently allocated thirds of an11/week quote cost
exactly11, even under low Decimal precision.

## Required inputs

A `CountBandRule` wraps the existing `ExclusiveQuoteRule`: exact jurisdiction,
employer/classification, unit, timezone, source/hash/citation, operative dates,
knowledge cutoff and reviewed interpretation. Its `bands` are finite inclusive
integer intervals with unique IDs and nonoverlapping bounds. Each priced band
names one declared component; all declared components are represented exactly
once. Gaps are permitted in the declaration but requested counts in a gap fail.

A band with `component=None` explicitly declares no entitlement for its finite
count range. This must be supported by the reviewed rule, not used to fill an
unknown table. For example, a source-defined minimum of two may support a0–1
no-entitlement band. A table ending at19does not authorize an unbounded last
band, a20-plus zero or a cap at19. No thresholds or real award rates are hardcoded
in the library.

`required_facts` names all required positive predicates. A `CountBandFact` has
its Boolean result, basis, evidence identity/hash, effective date interval, known
date and observed/scenario
kind. Every required fact must appear exactly once, including known negatives.
Unknown, absent, duplicate and additional predicates fail. All predicates are
AND-combined. Resolve any source-specific alternative, exception, counting rule,
appointment, qualification, service or selection test before supplying the
corresponding reviewed fact. A composite predicate such as selection-or-relief
is not computed from elapsed time by this method.

Each `CountBandCase` supplies an existing `QuoteExposureWindow`, a nonnegative
strict integer `staff_count`, the complete predicate set and an explicit
`count_and_facts_constant=True` assertion. The exposure's eligibility/history
flags qualify the window for consideration; they do not imply every allowance
predicate is true. They remain caller declarations, not independent verification
of evidence documents. Counts, facts and quantities must have their own actual
or scenario basis. Use opaque resource/evidence identifiers.

## Dates, quantities and failures

Count/fact changes need separate nonoverlapping windows and explicit quantity
allocation. The selected quote must match the band component/unit and cover the
whole local-date window. A price transition inside a window fails, even with
zero quantity or a known negative predicate; split upstream instead. Original
quantities remain in each selection. A failed predicate makes the payable quantity
zero while retaining the otherwise selected source price and negative fact IDs.

An explicit no-entitlement band has no selected quote and retains a zero selection.
It still requires all declared facts, qualified source/scope/knowledge, complete
exposure and nonduplication checks. A negative predicate cannot hide an unknown
count band. The existing exposure guard rejects duplicate IDs and overlapping
windows for one resource; different resources remain distinct. Deduplication
across separate calls is the caller's responsibility.

A fact must be known by the cutoff and its separate effective interval must
cover the whole window. Earlier knowledge is preserved; it need not be relabelled
as learned on the costing date. The exposure still requires complete observed
history through its window or an explicit scenario declaration;
analyst assumptions remain labelled scenarios. Scenario status propagates even
when a hypothetical predicate suppresses payment. Sources, releases, rules and
nested unchecked copies are revalidated. An explicit week stays a week across
DST: elapsed clock duration is not a quantity conversion.

## API and ledger

Load the reviewed `CountBandRule`, `UnitQuoteRelease` and tuple of
`CountBandCase` inputs, then call:

```python
from src.count_bands import price_count_bands

result = price_count_bands(rule, release, cases)
exact_total = result.prices.total
```

The returned `CountBandResult` retains method`count_band_quotes_v1`, the complete
validated rule/release, ordered cases, selected bands and quotes, all negative
predicates, exact per-case amounts and the shared price ledger/release hash.
Rational values are `Fraction` objects; choose any rounding separately.
[The synthetic regression fixtures](../tests/test_count_bands.py) demonstrate
complete input models, boundaries, dated prices, suppression and failure cases.

This is a Python library method. Existing CLIs and PSA are unchanged. It is not
a general payroll, automatic progression or staffing optimisation engine. Avoid
adding the result to a salary/hourly ledger already containing the same allowance.
A quote's annual/weekly denomination does not establish earned-period allocation,
payment timing, productive capacity or a cash saving. Actual source eligibility,
conflicting instruments and uncovered bands remain explicit acceptance work.
