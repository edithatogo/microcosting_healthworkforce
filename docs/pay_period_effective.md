# First-full-pay-period commencement

`first_full_period` resolves a reviewed rule whose supplied trigger is an aware
instant and whose effect starts at the first complete pay period beginning on
or after that instant. Supply the actual contiguous payroll boundary instants,
an explicit completeness assertion and a verified source for the stated scope.
The calendar must start at or before the trigger and include the end of the
selected period. The result preserves the rule and full calendar with the
resolved half-open interval; use its start as an input to a dated rate release.

The caller must choose the correct trigger, calendar and industrial interpretation.
This method does not derive a payroll cycle, determine eligibility, calculate
backpay or cash timing, or generalize one agreement's rule to another. For
example, the retained ACT administrative, support, technical and ambulance
editions each contain first-full-period wording in clause C2.2.2; applicability,
actual payroll boundaries and later variations require independent verification.
