# Pricing paid-leave exposure

`src.leave_pricing.price_paid_leave(release, selection, schedule, choices)`
connects the existing paid-leave schedule, selected historical-hours base and
direct unit quotes. It rebuilds both derived inputs from their original policy,
request and history. The leave and price scopes/knowledge dates must agree, and
the selected hours must refer to that leave commencement. Source admission and
review assertions retain their existing requirements; no real-worker eligibility
or current award rate is supplied by this module.

Supply one `LeavePriceSelection` for each exact interval in `schedule.rows`.
Its `pricing` is an `HoursPricingRequest` whose `week_quantity` equals that
row's `salary_equivalent_weeks`. The bridge checks equality rather than accepting
an independent multiplier. Half pay therefore scales salary hours once. The
returned `PricedLeave` retains the rebuilt schedule, hours selection, each
exposure/choice/source-priced component ledger, currency and exact Fraction total.

Select one valuation method explicitly on every choice:

- `dated_row_start` values the interval at its first date and requires every
  selected quote to cover the entire interval. Include quote-change dates in
  the original leave request's `split_on`; the bridge rejects an unsplit change.
- `explicit_snapshot` applies the supplied valuation snapshot and its stated
  basis. It can hold prices fixed for a counterfactual, even when the exposure
  lies beyond that quote's economic interval. The selected snapshot itself must
  still be covered by the accepted quote. This is not retrospective payroll due.

For a synthetic selected normal-hours base of `2100/73` hours per week, two
calendar weeks at half pay give one full-pay-equivalent week. At a constant
hourly price of 30 the exact salary exposure is `63000/73`. With one half-week
exposure at 30 and another at 40 it is `73500/73`. Splitting a constant-price
interval preserves its exact total; no Decimal context rounding is introduced.

Allowance quantities are supplied independently for each interval in its
`allowances` tuple. They retain their own unit, amount, basis and valuation date;
they are not multiplied by salary hours or the half-pay factor. The existing
base-inclusion, duplicate-component and exclusive-component guards apply.
Quantity IDs must also be unique across the whole episode. An allowance during
unpaid absence requires an explicit quantity and applicable price; no continuation
or proration right is inferred. To represent no added allowance, supply `()`.

Unpaid salary exposure is zero because the validated schedule explicitly says so.
Unknown accrual, entitlement offsets and remaining budgets stay null. Advance
payment remains a separate instruction and never creates an additional priced
quantity. This output is an economic price exposure, not an actual cash or payroll
ledger. KIT work/extensions, pay-cycle timing, progression, actual leave credits,
family/route eligibility and replacement cover require their separate rules.
The API neither applies a KIT extension nor reprices a contract automatically.

## Allocate a leave loading cap

Call `allocate_leave_loading_hours` with the eligible portions in payroll
order, the reviewed cap in hours and the hours already loaded in that cap
period. Use exact fractions for all three inputs. For a static scenario,
supply one eligible portion. For dated costing, supply ordered portions
split wherever the applicable loading rate changes. The result gives the
loaded hours for each input portion in the same order.

Price base leave pay for all applicable leave hours. Price the loading
increment using only the returned hours and the applicable rate for each
portion. Provide the correct cap period and starting consumption for each
run. Resetting prior consumption within one cap period can overstate loading.

## Price historical weekend leave credit

For the Victorian medical scientist agreement, group ordinary shifts by
weekend within one reviewed 12-month period. Pass each shift as
`WeekendLeaveShift` with its total ordinary duration and the ordinary hours
attributable to the weekend. Use `Fraction` values for both.

For example, an eight-hour qualifying shift with two hours attributable
to the weekend gives one hour of agreement leave credit. For a part-time
employee with qualifying shifts on both days, use the longer shift.
Equal-duration shifts with different weekend hours require a reviewed
selection before pricing. Pass any separately assessed NES shiftworker
credit in hours. The function returns the greater of that credit and
the capped agreement credit.

The resulting hours are a leave balance input. Use the applicable dated
salary and leave payment rules when valuing a later period of leave.
Confirm employer and classification coverage before applying the rule.

## Price historical NSW leave adjustments

For the general Conditions Award shift credit, pass the reviewed count
of ordinary Sunday and public-holiday shifts for one qualifying year to
`nsw_general_shift_leave_credit`. At 35 or more shifts the credit is one
ordinary working week. Below 35, the credit is prorated. A positive
prorated credit for a worker below 38 ordinary weekly hours also requires
the reviewed rounding increment in hours.

For deferred loading after advance leave, provide `AdvanceLoadingTiming`
with the entitlement date and evidence of continuing employment. Supply
separate weekly salary and benchmark quote IDs with `AdvanceLoadingPrices`.
`price_advance_loading` selects both rates at the entitlement date and
returns their ledger with the capped loading amount.

For separation, first establish the reason and the leave balance eligible
for loading. `price_separation_loading` uses that reviewed exposure and
requires explicit evidence for the valuation date. Advance ordinary-pay
excess is a separate calculation through `AdvanceLeaveTermination`, using
reviewed ordinary pay due and the relevant service-year completion date.
Its result is the excess before any payroll deduction.

## Reconcile a reviewed leave scheme credit

Use `LeaveSchemeReconciliation` and `net_leave_scheme_cost` from
`src.reimbursement` to calculate net employer cost for a matched case.
Supply original-worker leave pay, its paid on-costs, replacement labour
and the scheme credit in the same currency. Record the review evidence
with the case. For example, 100 of leave pay, 10 of on-costs, 50 of
replacement labour and an 80 credit leave 80 of net employer cost.

The credit is bounded by paid leave and its on-costs. Supply eligible
amounts from the applicable scheme and matched payroll evidence.
Retain the claim and cash receipt dates in the underlying records.
