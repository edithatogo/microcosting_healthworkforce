# Dated resource-hour quantities

`cost_dated_quantities` prices an explicitly supplied number of resource hours
across a dated interval. It complements `cost_dynamic`, which derives quantity
from elapsed activity time multiplied by resource count. Both use the selected
reviewed `CostRelease` and retain its source, scope and date admission checks.

For example, declare **one resource-hour** uniformly distributed over 11:00–13:00.
With $50/hour before noon and $70/hour after noon, the quantity is half an hour
at each price: $25 + $35 = $60. Two actual elapsed activity hours at one resource
would instead cost $120. A leave interval, payable quantity and actual productive
work must therefore remain separate inputs.

## Python API

```python
from datetime import UTC, datetime
from decimal import Decimal
from src.costing import DatedResourceUse, cost_dated_quantities

quantity = DatedResourceUse(
    quantity_id="scenario-quantity",
    resource_id="staff",
    allocation_id="synthetic-worker",
    starts_at=datetime(2026, 1, 1, 11, tzinfo=UTC),
    ends_at=datetime(2026, 1, 1, 13, tzinfo=UTC),
    hours=Decimal("1"),
    unit="resource_hours",
    distribution="uniform_elapsed_v1",
    quantity_kind="analyst_assumption",
    quantity_basis="Declared scenario quantity and uniform allocation",
)
# release must supply reviewed applicable hourly prices covering this interval.
result = cost_dated_quantities(release, (quantity,))
```

Units, quantity kind, distribution and a nonblank basis are mandatory. The kind
is `observed_use` or `analyst_assumption`; neither selects or proves entitlement.
A reference to evidence or an assumption belongs in `quantity_basis`. Use opaque
identities and avoid staff or patient details in shareable examples.

`DatedQuantityCost` retains the original typed quantities, an explicit
`uniform_elapsed_quantity_v1` method identity and the base hourly `CostResult`
ledger. Each wage-boundary row retains exact rational resource hours, price/source
lineage and component costs. Exact total fractions survive nonterminating splits
and low Decimal precision. Decimal fields remain display projections. Quantities
are sorted chronologically with identity as tie-breaker.

The calculation allocates each total by its segment's fraction of the interval's
UTC microseconds. A daylight-saving transition changes these weights, not the
declared total quantity. Constant prices reduce to static quantity costing.
Splitting a quantity into subintervals preserves cost only when the new quantities
preserve the selected allocation density; assigning arbitrary quantities changes
the scenario.

## Admission and limitations

Intervals must be positive and timezone-aware, and quantities finite and
nonnegative. Explicit zero still requires rate and source coverage throughout its
interval; uncovered periods do not become zero cost. Duplicate quantity IDs and
overlapping intervals for one explicit allocation are errors. An individual
allocation cannot have more resource hours than elapsed hours. Without an
allocation ID, quantities may describe a category containing multiple resources;
parallel or aggregate quantities remain the caller's responsibility. Overlap
checks cover this call's supplied quantities, not separate calls or other ledgers.

Uniform elapsed allocation is an explicit analytic convention. It does not
implement calendar-day, workday, roster, fortnight or payroll allocation. Supply
separate quantities at known boundaries when a qualified source provides a
nonuniform schedule. This API does not choose leave hours, historical-hours
averages, continuing allowances, half-pay, accrual, keeping-in-touch extensions,
backfill or payment dates. It does not price cases, trips or other non-hour units.
Unsupported distributions/units and release-required capabilities fail rather
than being approximated. This addition exposes a Python API; no CLI flag changes.

Use the source-qualified historical base and quantity rules before constructing
an actual paid-absence scenario. Payment, resource use, productive capacity and
cash savings are different outputs. Do not infer any of them from the width of
the selected interval or from a successful price calculation alone.

For replacement cover, an optional `covers_absence_id` retains a nonblank
caller-supplied absence reference on the dated quantity. Join the ledger
rows by their activity ID to the quantity ID to retrieve that reference.
The caller substantiates the link and the hours covered.

Pass `absence_hour_limits` to check the combined cover quantities in a
run against declared available hours by absence ID. Every linked quantity
must have a limit in that mapping when supplied. The result retains the
limits used and exact remaining hours by absence ID. Supply available hours after any cover accounted for outside
the run.
