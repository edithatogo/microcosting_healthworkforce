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

## Inaccessibility milestones and instalments

Use `price_inaccessibility_first_payment` and
`price_inaccessibility_recurring_payment` from `src.inaccessibility`
for reviewed single-category cases. Select an accepted annual quote
with unit `annum` and component `inaccessibility-category-N` for the
applicable category and valuation date. Supply the reviewed employment
fraction and evidence for eligible service and previous payments. Set
`service_assessed_through` to the last date covered by that assessment,
on or before the valuation date.

For the standard first milestone, categories 1–3 use six completed
eligible months and half the annual amount. Categories 4–7 use twelve
completed eligible months and the full annual amount. A completed,
unpaid recurring instalment after the initial milestone uses one
quarter of the annual amount. The supplied employment fraction applies
to each calculation. An unpaid, completed instalment at half time
therefore costs 150 from a synthetic annual quote of 1,200.

Provide a stable payment ID for each case so the resulting ledger row can be
matched to its payment history. This API prices a supplied case.
Calendar derivation, mixed-category service and vocational rotation
eligibility require separate evidence and methods.

For a reviewed single-category vocational RMO rotation case,
`price_inaccessibility_rotation_payment` applies the four-completed-month
threshold within the declared service year. The service assessment date
must fall within that year. Supply the reviewed annual
fraction as a decimal or exact fraction, separately from the employment
fraction. The calculator checks the supplied prior-payment status.
