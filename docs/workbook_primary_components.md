# Historical primary workbook component lineage

The candidate profile names the monetary and share columns in the five
jurisdiction blocks of `Labour - Prices`. The mapping is bound to the original
workbook hash. The accompanying check compares all 600 component formulas for
25 jurisdiction-role rows with their source references.

Superannuation, penalties, private-practice and attraction/retention inputs,
sick leave and leave loading are multiplied by midpoint salary. Professional
development is carried as a fixed annual value; annual leave uses weeks divided
by 52, multiplied by midpoint salary. The workbook's percentage tables divide
each corresponding amount by midpoint annual cost. Lower and upper salary bounds
are alternative salary values, not additional components to add to midpoint
salary. Their displayed shares use that same midpoint cost denominator.

The names describe the historical workbook's arithmetic and labels. They do
not establish award applicability, actual leave replacement expenditure,
eligibility or a validated contemporary cost. Candidate metadata is not an
accepted conditions release, and archived proxy components must not be added
automatically to nominal-hour costing.

The historical `ALL` rows use a different basis: they average the five
jurisdiction input fractions, then multiply by the first jurisdiction's
midpoint salary. Fixed allowances and salary bounds are averaged instead. This
is not generally the mean of the jurisdiction-specific component amounts and
does not establish an intended or accepted national average.

A private LibreOffice recalculation independently reconciled all 600
mapped outputs across the 25 jurisdiction-role rows. The comparison
covered the annual amounts and midpoint-cost shares, using the
recalculated input operands and a tolerance of 0.00000001 in the
respective output units. This check covers the jurisdiction blocks.

The replay also matched all 60 `ALL` annual component amounts and
all 60 formatted share strings. The share strings use the first
jurisdiction's midpoint-cost denominator for the mean, minimum
and maximum, then format each result to one decimal percentage point.
These are historical display ranges.

The `Assumptions` sheet at A2:B2 identifies the public-holiday input as
an average across years and within each state. The historical calculation
uses that salary-linked proxy. An activity ledger needs the dated holiday
classification, actual hours and applicable instrument before pricing any
holiday payment or time credit.
