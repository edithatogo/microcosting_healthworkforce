# Whole-period contribution comparisons

`src.period_contributions` implements `aggregate_then_greater_total_v1` for
one or more reviewed contribution definitions. Each alternative names its own
hourly earnings components and effective-dated fraction schedule. The library
sums each alternative over one explicit comparison period, then selects the
largest **period total once**. It retains losing alternatives and all ties.

For example, two hours earn salary of $100 each. Only the first hour earns a
$100 supplement. A broad alternative is 10% of salary plus supplement; a narrow
alternative is 15% of salary. Broad is $20 + $10 = $30; narrow is $15 + $15 = $30.
The contribution is $30 and base plus contribution is $330. Choosing the larger
amount independently each hour would incorrectly charge $35.

## Python interfaces

Create a `ContributionPeriod` with a stable period/resource/allocation identity,
aware start/end instants and `earnings_complete=True`. This assertion belongs
to the caller: it means all relevant earnings are supplied, including carry-in
where required by the selected comparison period. An empty complete period is
zero earnings; missing history cannot be represented as an empty period.

Create a reviewed `ContributionRule` with an output component, effective local
dates, timezone, source identity/hash/citation and one or more
`ContributionAlternative` definitions. Each alternative supplies explicit base
component names and reviewed `ContributionFactor` intervals. Sources must cover
the exact employer, jurisdiction, classification and entire comparison period.
Every relevant rate must contain every required base, including explicit zeros
for known absent components. Missing components are errors. For a levy with one
reviewed basis, supply a single alternative. Its total is the selected amount.
Periodic allowance payments require a separately dated posting and assignment
binding before they can be included in a paid-earnings basis.

Call `cost_contribution_activities(release, period, rule, activities)` for
complete earned activities. Wage and factor changes split the candidate ledger
independently. Activity order does not change totals. Activities must fit inside
the period and refer to one resource, one physical allocation and a resource
quantity of one. Duplicate/overlapping work is rejected by the base costing
contract. Elapsed time uses UTC microseconds and exact rational arithmetic;
no Decimal tolerance or intermediate money rounding changes the selected total.

Call `cost_contribution_snapshot(release, period, rule, at, resource_use)` for
an explicit complete quantity at one assumed snapshot price. Each alternative
must have a single factor covering the period, and quantity cannot exceed its
elapsed hours. This mode is a constant-price quantity scenario. Use earned
activities when factor or actual wage timing matters.

Both functions return `PeriodContributionCost`: the unchanged base cost ledger,
comparison period/rule, candidate rows with factor and rate lineage, every
alternative's exact `Fraction` total, all winning identities, one exact selected
contribution and exact combined total. The selected contribution is separate
from base components. A release already containing its named output component
is rejected to prevent charging it twice. This Python API does not add a CLI mode.

## Reviewed earnings caps

A contribution alternative can carry a `ContributionCap` with a reviewed
source, a limit, a cap window and prior eligible earnings through the start
of the costing period. Supply an explicit zero when the period starts at
the cap window boundary. The source must cover the entire cap window and
the costing period must fit inside it.

The calculation consumes the remaining earnings base in chronological order.
The ledger keeps both the gross `base_amount` and the `eligible_base_amount`
used for capped pricing. For example, a 62,500 limit with 60,000 already
earned leaves 2,500 available. If the period adds 5,000 of eligible earnings
at 12%, its capped contribution is 300. Each alternative is priced separately
before comparing totals.

## Applicability and limitations

The caller must substantiate the comparison period, eligibility, selected bases
and fractions from the governing instrument. Resource employer/classification
scope is fixed over the period. Review flags and hashes bind supplied evidence;
they do not independently establish legal correctness or completeness of earnings.

This method values earned hourly components. It does not infer payment dates,
statutory ordinary-time earnings, statutory cap selection, credits, retrospective payroll,
minimum contributions, individual written arrangements or rounding conventions.
Explicit `required_capabilities` outside this method are rejected. Select another
qualified method when these conditions matter; do not silently omit them.

In particular, the unresolved Queensland VMO superannuation source chain is not
promoted by these synthetic tests. No universal rate, common base or VMO worker
eligibility is supplied. This capability supports testing a later verified rule;
actual source and arrangement qualification remains a separate task.

A period may retain an explicit `planned_remittance_at` timestamp at or after
its end. This is a timing assumption carried with the ledger. Pricing still
uses the earnings period. The timestamp does not establish a due date or
record a completed payment.

## Queensland medical officer vehicle allowance

For a reviewed MOCA7 scenario, clause 2.7.4 calls for comparing the
Commonwealth and Queensland employer contributions. Configure each
alternative with its own dated base, factor and applicable cap. Compare
the calculated amounts over the same reviewed period. The Commonwealth
and Queensland rates alone cannot determine which amount is greater.

Clause 11.33 describes a recurring cash payment in lieu of a supplied
vehicle. Keep it separate from reimbursement of work-related vehicle
expenses. For each alternative, resolve the payment's treatment against
the dated earnings definition and employee category. The Queensland
regulation distinguishes employer salary under section 4 from
superannuable salary under section 5. Apply the definition referenced
by the selected contribution row, including any applicable section 15
agreement. For a paid-earnings calculation, qualify the allowance's
payroll posting and assignment binding before including it.

Use `reconcile_allowance_payment` to compare a priced periodic
allowance with a caller-matched payroll posting. Pass that reconciliation
through `allowance_reconciliations` in `cost_contribution_payments`, and
pass the remaining postings through `payments`. Together they must cover
the complete period. Each reconciled posting enters the calculation
through its reconciliation. Supplying it in both arguments raises a
duplicate payment error.
It retains any paid-versus-payable difference and prices the actual
posting against each reviewed base that includes its component. This
keeps the allowance calculation and its cash posting separately auditable.

## Queensland long-service leave levy

The [Treasury Central Scheme guidelines](https://www.treasury.qld.gov.au/files/Long-Service-Leave-Central-Scheme-Guidelines-2.pdf)
distinguish monthly expense recognition from quarterly remittance.
Use a single contribution alternative for a reviewed levy base. For
monthly costing, price each month using its eligible gross earnings.
Aggregate those expenses for the quarter and retain the remittance
date separately. The engine preserves an explicit planned remittance
timestamp. A statutory due date requires the applicable working-day
calendar and the agency's remittance schedule.

Confirm member agency coverage, employee eligibility and payroll
component mapping before setting the base. The historical workbook
includes the vehicle allowance. A current levy calculation requires
evidence that the agency includes that payment in eligible gross
salary. Keep claims for leave paid separate from levy expenses.

## Historical Queensland workbook reconciliation

In the recalculated Senior Medical Officer diagnostic, 24 assignment
months had positive vehicle allowance. Independent component sums
reproduced all 96 downstream results for superannuation, long-service
leave levy, WorkCover and total cost within AUD 0.00000001.

The workbook includes vehicle allowance directly in each on-cost
base. Its WorkCover calculation also includes superannuation and
long-service leave levy. Preserve those dependencies when reproducing
the historical model. For current WorkCover costing, classify the
payment against the applicable premium guidance. The [WorkCover
wages manual](https://www.worksafe.qld.gov.au/__data/assets/pdf_file/0014/17240/wages-definition-manual.pdf)
distinguishes remuneration from reimbursement of work expenses.

Central West HHS's [2024–25 financial statements, notes B2-1 and B2-2](https://www.centralwest.health.qld.gov.au/__data/assets/pdf_file/0018/450702/central-west-hhs-annual-report-2024-2025.PDF)
show separate premium costs for directly employed staff and charges
for staff supplied by the Department of Health. When costing supplied
staff from the HHS perspective, use the applicable service charge.
When consolidating the HHS and Department perspectives, eliminate the
internal recharge and retain the external premium once. The annual
report establishes the accounting pathways. A dated policy or service
charge schedule is needed to price an individual assignment.

A reviewed fixed service charge can be priced as a dated unit quote
using the service agreement as its source. A reviewed percentage charge
can use a single contribution alternative with the agreement's explicit
earnings base. Keep the recharge and insurer premium in distinct
components and ledgers. These pricing APIs calculate the separate
charges. Consolidation and verification of matching inter-entity entries
require a separate accounting step.
