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

The separate `microcosting-healthworkforce-v2` command accepts a condition-release
JSON file, an activity JSON file, a local IANA timezone and an output path:

```sh
microcosting-healthworkforce-v2 --release release.json --activity activity.json \
  --timezone Australia/Brisbane --output result.json
```

It validates both input schemas and creates a new result file exclusively; it
will not overwrite an existing result. The command uses the limited method and
source assertions described above. The original CLI remains unchanged.

## Explicit cumulative overtime

`src.roster_costing.cost_overtime_period` supports one specified resource in one
explicit pay period. The caller supplies a reviewed, source-linked threshold and
salary-only multiplier, the complete eligible activity list, prior eligible hours,
and a history boundary at the first activity. The method rejects overlapping
activities, missing history, uncovered rule dates and source-hash mismatches.
It applies the multiplier increment to salary only; other components are unchanged.
Totals retain each segment's conditions, rule ID, citation and source hash.

This is a narrowly defined arithmetic method, not an award interpreter. It does
not decide eligibility, reconstruct pay-period history, determine whether all
activities are eligible, calculate multiple overtime tiers, apply minimum
engagements, or combine penalties. The caller's completeness and review assertions
must be supported outside the calculation. Unsupported combinations must remain
outside this method until their actual interaction is modelled and verified.

## Paid capacity and replacement-cover scenarios

`src.capacity_costing.capacity_scenario` calculates paid cost from a dated
condition release and subtracts explicitly supplied, disjoint lost hours from
the original worker's paid hours. It adds explicitly supplied incremental cover
hours and cost once, and records those inputs as scenario assumptions rather
than industrial entitlements. The cost-per-productive-hour denominator describes
the original worker only; any productive output from replacement cover is not
included. It does not infer leave uptake, cash savings, overlap between absences,
or the cost or productivity of cover.

`src.tiered_overtime.cost_tiered_overtime` extends the same explicit-period
method to strictly increasing cumulative thresholds with nondecreasing total
salary multipliers. It counts base cost once and reports each incremental
premium. Hours above a later threshold also appear in earlier threshold totals;
these are cumulative, not mutually exclusive bands. Decreasing multipliers,
shift-specific thresholds, premium stacking and minimum engagements are not
supported by this method.

## Explicit minimum engagement

`src.minimum_engagement.cost_minimum_engagement` supports one explicitly eligible
engagement contained within a local calendar date. It pays all base components
for worked hours and adds any guaranteed minimum hours using only the components
specified in the reviewed rule. It rejects unknown components, uncovered source
or rule dates and unconfirmed eligibility. Additional hours use the local-day
rate as a declared allocation method; their actual timing is not inferred. This
method does not combine the minimum with overtime, shift penalties, multiple
engagements or changes across local dates.

Flat-rate and condition-activity results also expose `exact_total_numerator` and
`exact_total_denominator`: an unrounded rational total calculated directly from
the supplied decimal conditions and elapsed microseconds. The existing Decimal
`total` and component segments remain for compatibility and can differ by small
context-precision amounts when hours or annual rates do not terminate in base ten.
Callers should combine the rational totals before applying a declared rounding
policy when exact aggregation is required. The cumulative overtime and tiered overtime results also provide exact rational
totals; their existing Decimal fields retain context-precision behaviour. The
minimum-engagement and capacity scenario methods also expose exact rational
totals; the capacity scenario additionally exposes its exact productive-hour rate.

## Exact aggregate presentation

Flat-rate ledger rows retain `exact_hours_numerator` and
`exact_hours_denominator`, alongside their Decimal hours. Dynamic row hours use
exact elapsed microseconds and resource quantities; static rows retain the
supplied exact Decimal quantity as a rational number. Components are aggregated
from exact hours and source rates before each aggregate amount is projected once
to Decimal. The total is projected from the exact rational total, rather than
summing rounded Decimal row amounts.

Splitting an activity therefore preserves aggregate component amounts and the
reported total within the same Decimal context. Row-level Decimal amounts and
their sum can differ in final representation digits from a once-projected
aggregate; the rational quantities and exact total remain the accounting oracle.
This is numerical projection, not a currency-rounding policy. No industrial
rounding, cents allocation or payroll payment rule is inferred. Previously
serialized rows lacking exact hours must be recomputed from their source inputs,
rather than inventing zero or treating rounded hours as exact originals.
## Direct quoted units and dated events

`src.unit_quotes.price_units` prices explicit `QuoteQuantity` inputs against an
accepted `UnitQuoteRelease`. Each input names its quote, exact denominator unit,
valuation date, nonnegative quantity, provenance kind (`observed_use` or
`analyst_assumption`) and basis. Quantities at one date form a static snapshot;
quantities at different dates form a dated event series. Results retain the full
quote/source citation, quantity, release hash and exact `Fraction` amounts.

For example, a synthetic price of 100.01 AUD/fortnight and an independently
published 2700 AUD/annum can coexist. One fortnight costs exactly 100.01; one
annum costs exactly 2700. Neither quote is converted to the other. A quantity
of 0.5 fortnight must be supplied with its reviewed basis; the library does not
infer it from seven elapsed days, part-time hours or an annual divisor.

The release requires held primary sources with verified employer/classification/
jurisdiction scope, matching hashes, full effective-interval coverage and a
knowledge date covering source retrieval and the quote's known-from date.
Candidate quotes, overlapping same-component/unit versions, duplicate identities,
wrong units and dates outside a named quote are rejected, including for zero
quantities. Explicit quote IDs prevent silent substitution of another version.

This is direct price application. Worker eligibility, mutually exclusive
allowances, award comparisons, alternative payment arrangements, actual payroll
accrual/payment dates and partial-period allocation remain separate reviewed
inputs. A quantity spanning a price change must first be allocated by an explicit
qualified method. Annual and fortnight inputs must not represent the same cost
twice; no automatic combination with hourly/fixed-annual ledgers is performed.
The API does not assert a source-specific payroll rule, a full employment cost,
or empirical PSA validity. No real source rates or private records are bundled.

## Complete historical-hours comparison

`src.historical_hours.select_normal_hours` supplies the quantity-base step for an
explicitly selected twelve-month/forty-week comparison method. It compares an
exact historical weekly average with commencement weekly hours and retains both
comparands, the winner (including a tie), original history rows, rule/source and
normalization declarations. It does not calculate monetary normal pay.

For at least twelve calendar months of verified continuous service, the method
uses the preceding calendar anniversary window. For shorter service of at least
forty weeks, it uses the whole service interval. The anniversary clamp convention
must be selected explicitly, including its treatment of leap day. This convention
is an execution choice requiring review; the library does not claim it is mandated
by every instrument. Service eligibility outside the selected comparison and all
employee/leave-route conditions remain upstream decisions.

Supply fully allocated `HistoricalHours` rows covering that exact window, including
explicit zero periods. Missing rows, gaps, overlaps, duplicate identities and rows
outside the selected window fail; the engine does not clip or distribute a total
across a boundary. History completeness and continuous-service verification must
also be asserted. The rule admits only matching held-primary source scope/hash
and a covered commencement date, with an explicit knowledge date.

The averaging exposure is a mandatory rational number of equivalent weeks with
its own kind (`reviewed_payroll_exposure` or `analyst_assumption`) and nonblank
basis. No value of 52, 26 or calendar days divided by seven is inferred. In a
synthetic calendar-day/7 scenario, 1500 hours over 365/7 weeks yields exactly
2100/73 hours/week; comparison with 20 selects the historical mean. Choosing a
payroll exposure instead remains an explicit input requiring source qualification.

This quantity selection does not choose wage rates or continuing allowances,
interpret service credit, establish variable-part-time/parental eligibility,
calculate leave accrual/payment, or infer cover/cash savings. The unresolved source
normalization convention remains visible even when a scenario's arithmetic passes.
No real employee histories or private instrument extracts are bundled.

## Exact selected-hours pricing and allowance interactions

`QuoteQuantity.quantity` accepts a nonnegative finite Decimal or an exact
Fraction. Existing Decimal inputs keep their behavior. Fractions remain exact
through pricing and JSON roundtrip, with no conversion to a context-rounded
Decimal quantity. Use `model_validate_json` for JSON; runtime revalidation retains
raw typed fields so an unchecked Python float copy is still rejected.

`src.normal_pay.price_selected_hours` connects a `NormalHoursSelection` to an
explicit `HoursPricingRequest` and accepted `UnitQuoteRelease`. It recomputes the
selection from its original rule/request/history, requires matching source scope
and knowledge date, and multiplies selected hours/week by the supplied exact week
quantity and an explicitly named hour quote. The request's valuation date selects
the applicable price; it does not assert a cash date or earned leave period.
Repeated calls can price separately qualified dated exposure partitions.

Supply additional allowance `QuoteQuantity` records separately in their own
source units at the same snapshot. A fixed fortnight quantity is not scaled a
second time by salary hours or the week exposure. Caller-declared base inclusions
and their basis are mandatory; an allowance already included in the base or a
second quote for the same component is rejected. Explicit exclusive-component
groups and an interaction basis are also mandatory (an empty tuple is a deliberate
no-groups declaration). Alternative categories cannot be combined, including when
one is already loaded into the base or has a zero supplied quantity. The engine
does not discover these source-specific groups from component names.

For the existing synthetic 2100/73 hours/week selection, one explicit week at
30 AUD/hour costs exactly 63000/73 AUD. A separately supplied half-fortnight at
100.01 AUD/fortnight adds exactly 10001/200 AUD. Results retain the recomputed
selection, exposure/inclusion/interaction declarations, source quotes and exact
component ledger. Monetary results are price exposures, not an assertion of pay
due. Eligibility, continuing status, allowance proration, calendar normalization,
paid/unpaid leave/accrual and employment endpoints remain separate qualifications.

## Paid-leave exposure state

`src.paid_leave.build_paid_leave` builds a dated ledger from an explicitly reviewed
`PaidLeavePolicy` and approved `PaidLeaveRequest`. Calendar absence, normal-pay-
equivalent salary exposure, accrual eligibility and entitlement-budget debits are
separate axes. Full pay uses the declared paid weeks; the selected half-pay option
spreads that exposure over twice the calendar duration. An advance election records
a separate caller-supplied earlier payment instruction, without adding a second
salary exposure or valuing actual cash.

The explicit calendar-days/7 convention and its basis are mandatory. Policy,
accrual-cap and caller split boundaries partition the approved episode. Half-pay
exposure beyond the independently declared accrual cap does not accrue additional
eligible weeks. An unknown paid cap or unpaid accrual factor remains null; the
known accrual subtotal is retained separately and is not an actual accrued-leave
credit. No twenty-working-day rule is inferred from calendar days.

Entitlement offsets require a review kind and rationale. An unresolved offset
leaves debit/remaining-budget outputs null. Calendar-absence and normal-pay-
equivalent debit scenarios can be supplied explicitly, without implying either
is the correct interpretation of a particular instrument. Calendar absence limits
remain independent. Fixed-term episodes require a covering contract endpoint;
only an explicitly approved shorter endpoint truncates the planned exposure,
with unused salary-equivalent budget retained. It is not forfeiture or cash due.

All policy/approval/eligibility declarations and source scope/hash/date/knowledge
are validated. There is no default approval, employee classification, payroll
rounding or cash date. Keeping-in-touch work/extensions, family/route interactions,
other leave and approved extension processes need their own qualified state rules;
they must not be inferred from this core profile.

To price these exposures, partition rows at every applicable price boundary,
select covering quotes and pass each row's exact `salary_equivalent_weeks` to
`price_selected_hours` as its explicit week exposure. Supply allowances separately
with their own qualified units/continuation basis. The full and half profiles have
equal constant-price salary exposure; a wage increase during the longer half-pay
period can make their dated prices differ. This is exposure costing, not the
valuation or execution of an actual advance payroll payment.
