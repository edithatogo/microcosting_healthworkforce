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
