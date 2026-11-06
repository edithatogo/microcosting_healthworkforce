# Source-qualified crib-away occasion pricing

`src.crib_away.price_crib_away(rule, release, shift, occasions)` validates one
complete, explicitly eligible shift and delegates monetary arithmetic to the
existing `price_units` calculator. It constructs exactly one unit per directed-away
occasion. Source prices may distinguish shifts entitled to one crib from those
entitled to two: the two-crib price is each, not one bundle covering both breaks.
Published cent differences between alternatives remain visible.

## Required inputs

`CribAwayRule` names the policy source/hash/citation, reviewed operative interval,
knowledge date, exact release scope, local timezone, denominator unit and distinct
one/two-entitlement component names. `interpretation_kind` and
`interpretation_basis` state whether the supplied entitlement/occasion-date method
is source-reviewed or an analyst assumption. The policy source must be present
and applicable in the price release independently of its monetary quote sources.
No source, component or applicable rate is inferred from a role name.

`CribShift` supplies opaque shift/resource IDs, aware start/end instants, one or
two `entitled_cribs`, verified eligibility and entitlement with their bases,
complete-history assertion, evidence ID/hash and knowledge date. Inputs are
`observed_case_evidence` or `analyst_assumption`. Verified declarations require
upstream evidence; the function does not independently certify them.

Qualify rostered duration, employment/service membership, break windows and any
permitted agreement/exception before supplying entitlement. Elapsed UTC hours
need not equal the source's roster-hours measure, especially across DST. This
method does not silently select a 12-hour threshold, extrapolate longer shifts,
or replace missing source eligibility with a default. It validates the explicit
qualified entitlement rather than deriving all legal conditions from timestamps.

Each `CribOccasion` supplies a unique break ID, matching shift ID, integer slot,
aware `occasion_at`, explicit boolean `directed_away`, evidence kind/ID/hash,
knowledge date and basis. Include every entitled slot exactly once, even when
not directed away. A directed occasion requires `quote_id`; a known non-away
slot requires null. Missing slots and unknown direction cannot become zero.
The reference instant identifies that occasion's selected valuation date; it
does not claim an actual completed 30-minute break or a payroll payment date.

## Validation and dates

The function rebuilds all input models, including nested release data. Case/
policy review, source/quote hashes, exact employer/classification/jurisdiction,
knowledge dates and whole-shift policy coverage are checked. Duplicate IDs/slots,
extra/missing slots, foreign-shift rows, outside-shift reference instants and
non-increasing slot times fail. Reversed input-list order is normalized by slot.
Integer slots and constructed one-unit quantities prevent fractional/excess
break payments. The selected quote must have the exact context component and
unit; a single-crib quote cannot be used for a two-entitlement shift or vice versa.

Each directed occasion is valued on its reference instant's date in the explicit
local timezone. The existing price function checks the selected quote's half-open
coverage and release sources. Thus an overnight shift may use old and new quote
versions for different occasions. The caller must qualify this valuation method
and the source-effective pay calendar; the library does not assume a date change
means a universal payroll rate change or select a quote automatically.

Observed complete-shift and occasion evidence cannot predate the corresponding
shift/occasion date or exceed the knowledge date. Future projections require
explicit assumption labels. Any assumption in policy interpretation, shift or
slot evidence makes the overall result `scenario`. `reviewed_case_inputs` retains
supplied evidence labels and does not constitute an independent payroll audit.

## Output and accounting boundaries

`CribAwayResult` retains method/rule identity and rule hash, complete shift and
ordered occasion evidence, directed count, mode and the shared exact price ledger.
Known non-away slots stay in the evidence. If all are known non-away, the price
ledger is empty with exact zero, while case/policy checks still apply. Result
quantities contain the original break ID and source-linked selected quote.
Fraction totals remain exact even under low Decimal precision.

For example, synthetic each-occasion prices 11.01 and 5.51 produce 11.01 for one
occasion under single entitlement, 5.51 for one under two entitlement, and 11.02
for two under two entitlement. No equality is forced between those alternatives.
An old-price occasion at 5.01 and a new-price occasion at 5.51 total 10.52.
These numbers illustrate arithmetic and do not select a jurisdiction's rates.

This ledger prices only the directed-away allowance. Paid break salary, productive
capacity, missed/incomplete-break ordinary-time payments, overtime, on-costs and
cash are separate. Do not deduct paid break salary or add it again merely because
an allowance is priced. Repeated calls or combined ledgers require the caller to
prevent duplicate shifts/resources/economic costs across runs. Actual source
qualification, roster/exception evidence, calendar and complete direction history
remain prerequisites for real-case use; no source data is distributed here.
