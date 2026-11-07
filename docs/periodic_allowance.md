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

For reviewed concurrent or sequential service across categories, pass
one `InaccessibilityCategoryPayment` per payable share to
`price_inaccessibility_category_payments`. Supply the applicable
annual quote, a unique payment ID and the reviewed annual fraction
as a `Fraction`. Keep employment proration separate. For example,
a reviewed one-third annual share at half time prices one-sixth of
that category's annual quote. The assessment evidence should identify
the qualifying engagements and prior payments. Use distinct payment
IDs for distinct instalments so the resulting rows can be reconciled.

## Transfers across releases

For a transfer across releases, use
`cost_periodic_allowance_across_releases(component, period, allocations)`.
Each allocation pairs the segment with its applicable condition release.
Supply the same allowance component and the parent denominators throughout.
The schedule preserves each segment's release ID and hash and checks the
classified hours and factors across the whole payroll period. The caller
supplies the reviewed assignment and facility evidence for each segment.

## Queensland medical vehicle allowance

Use `moca7_vehicle_level` with a reviewed SMO or MPPP appointment
covered by MOCA7 clause 11.33.2. Supply the actual classification
and the level of Medical Manager's Allowance received. A zero means
reviewed nonreceipt. Resolve missing receipt evidence before selecting
a level for a grade 13–24 appointment.

Use the selected level to identify the accepted annual vehicle
condition for the service period, then pass that condition's component
to the periodic costing API. Supply the reviewed fortnight denominator
and allocate ordinary hours and paid leave at their applicable pay
fractions. Unpaid leave has a zero payment factor. If the appointment
or manager allowance changes within a fortnight, use
`cost_periodic_allowance_allocations(period, allocations)`. Supply
one tuple of release, selected component and period segment for each
effective interval. The segments must cover the whole fortnight in order,
retain its full-time hours and annual divisor, and reconcile the hours
for every label and pair of accrual and payment factors. Retain the
appointment and receipt evidence for each selection.

The Queensland Labour comparator reselects the vehicle level using each
month's progressed pay point. The FTE comparator keeps its initial level.
Record which behavior a workbook comparison uses. For MOCA7, select a
level from the reviewed appointment for each effective interval. The
workbooks' projected rate increases are separate from that selection.

[QIRC certified MOCA7, clause 11.33](https://www.qirc.qld.gov.au/sites/default/files/2025-11/2025_cb128.pdf)

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

## EDON recurring vehicle allowance

For an appointment verified under Queensland Health C24, use the dated SES
amount and classify the period into paid, half-pay and unpaid leave portions.
The policy pays the vehicle allowance in full during paid leave, at half
rate during half-pay leave and at zero during unpaid leave. Keep these
payment factors separate from any independently established accrual factors.

Exclude this component from the superannuation, annual leave loading and
termination payment bases when applying C24. Use separate travel quantities
for authorised private-vehicle travel.

[Queensland Health policy C24, sections 1 and 1.4](https://www.health.qld.gov.au/__data/assets/pdf_file/0026/164078/qh-pol-176.pdf)

## Payroll assignment binding

Set both `resource_id` and `allocation_id` on an allowance period to
bind it to a payroll assignment. Every segment of a bound schedule
carries the same pair. Payment reconciliation checks that the payroll
posting has those identities. For unbound periods the caller supplies
the assignment match.
