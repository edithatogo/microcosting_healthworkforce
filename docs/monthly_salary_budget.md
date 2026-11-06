# Calendar-month salary scenario

`monthly_salary_budget` divides an analyst-supplied annual salary by 12 and
prorates each month by the number of inclusive covered calendar days divided by
the number of days in that month, then applies the supplied FTE. It returns exact
fractions and a row per month with the rate identity and day counts. Rates must
cover whole calendar months and may not overlap; a gap fails closed. No rounding
is applied, and zero salary or FTE remains a genuine zero.

The method is a planning scenario. Salary inputs and month boundaries are chosen
by the caller; it does not establish award applicability, source lineage,
payroll amounts, leave, on-costs, pay-point progression or a rounding policy.
It is separate from elapsed-hour roster costing and does not assert full parity
with any workbook. Where a source rate changes within a month, this method cannot
represent the change and requires a different qualified method.
