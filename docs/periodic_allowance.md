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

The entire period must be covered by one accepted condition. Split periods
explicitly at changes. Labels, hours and factors are caller assertions: this
API does not determine eligibility, payroll dates, leave, overtime, policy
history or individual entitlements. Allocation hours may not exceed the
specified full-time hours. This is a separate calculation, not a cash-flow model;
do not add it to an hourly cost ledger already containing the same allowance.
