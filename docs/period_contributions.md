# Whole-period contribution comparisons

`src.period_contributions` implements `aggregate_then_greater_total_v1` for
reviewed alternative contribution definitions. Each alternative names its own
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
dates, timezone, source identity/hash/citation and two or more
`ContributionAlternative` definitions. Each alternative supplies explicit base
component names and reviewed `ContributionFactor` intervals. Sources must cover
the exact employer, jurisdiction, classification and entire comparison period.
Every relevant rate must contain every required base, including explicit zeros
for known absent components. Missing components are errors.

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

## Applicability and limitations

The caller must substantiate the comparison period, eligibility, selected bases
and fractions from the governing instrument. Resource employer/classification
scope is fixed over the period. Review flags and hashes bind supplied evidence;
they do not independently establish legal correctness or completeness of earnings.

This method values earned hourly components. It does not infer payment dates,
statutory ordinary-time earnings, quarterly caps, credits, retrospective payroll,
minimum contributions, individual written arrangements or rounding conventions.
Explicit `required_capabilities` outside this method are rejected. Select another
qualified method when these conditions matter; do not silently omit them.

In particular, the unresolved Queensland VMO superannuation source chain is not
promoted by these synthetic tests. No universal rate, common base or VMO worker
eligibility is supplied. This capability supports testing a later verified rule;
actual source and arrangement qualification remains a separate task.
