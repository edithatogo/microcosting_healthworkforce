# Explicit periodic allowances

`cost_periodic_allowance` allocates one accepted `fixed_annual` condition across
caller-supplied ordinary-hour portions for a half-open payroll period. The caller
provides the full-time period hours, periods per year, labels and separate
accrual and payment factors. The output preserves each portion, source-linked
condition, and exact rational accrual and payment totals; callers choose any
rounding and presentation.

For example, an accepted full-time annual allowance of $1,975, 30.4 ordinary
hours, 76 full-time hours and 26 periods yields exactly $395/13 per period,
which displays as $30.38 when rounded to cents. The caller must select and
justify the period divisor; it is not inferred from a calendar or an annual
amount. A half-pay portion can use distinct accrual and payment factors if the
applicable source supports those assumptions.

Each interval passed to `cost_periodic_allowance` needs one accepted condition
that covers the entire interval. Use `cost_periodic_allowance_schedule` when a
nominal period contains a rate change. Pass the whole period and its ordered
segments. The segments must cover the period contiguously, retain its full-time
hours and annual divisor, and conserve allocated hours for every combination
of label, accrual factor and payment factor. The result retains each segment
and sums exact accrual and payment amounts separately.

Use the condition's actual effective date when splitting. For an increase due
from the first pay period starting on or after 1 July, a fortnight starting
24 June keeps its existing rate throughout. The new rate starts on 8 July
if that is the next period on the supplied payroll calendar.

Supply reviewed eligibility, payroll dates, hours and factors. Allocation
hours may not exceed the specified full-time hours. When combining ledgers,
count the allowance once.

For a transfer across releases, use
`cost_periodic_allowance_across_releases(component, period, allocations)`.
Each allocation pairs the segment with its applicable condition release.
Supply the same allowance component and the parent denominators throughout.
The schedule preserves each segment's release ID and hash and checks the
classified hours and factors across the whole payroll period. The caller
supplies the reviewed assignment and facility evidence for each segment.

## Receipt-based vehicle travel exclusion

Use `src.vehicle_allowance.price_vehicle_travel` for a reviewed rule
that excludes an Award kilometre payment when the worker receives
a recurring vehicle allowance. Supply the exclusion source and hash,
travel component, effective interval and knowledge date. Each travel
case supplies explicit receipt or nonreceipt evidence for the worker
and valuation date. The result retains suppressed cases and prices
the remaining kilometres against the applicable release.

Value the recurring allowance separately using its own payable
period and leave portions. The caller must match the receipt evidence
to the worker and travel date.
