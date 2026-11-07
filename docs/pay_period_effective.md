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

For a later source that explicitly authorizes an earlier entitlement interval,
attach a reviewed `RetrospectiveAuthority` to the rule with the bounded
entitlement dates, when that authority became known, the run's knowledge cutoff
and a citation. The source must be verified for the same scope at both the
known-from and as-known-at dates, and the source hash must match. Earlier trigger
and selected period-start dates must lie inside the reviewed interval. Without
that assertion, ordinary source-date checks remain unchanged. The authority is a
caller-reviewed assertion; the resolver does not determine whether the source
actually grants retrospective effect. A condition release can price reviewed retrospective entitlements in
snapshots and dated activities when its knowledge date matches the authority.
Entitlement pricing, payroll backpay settlement and cash timing are separate
calculations.

For a reviewed payroll adjustment, pass matched entitlement and credited amounts
to `reconcile_adjustment` in `src.adjustment_settlement`. Each line identifies
its component, half-open interval and evidence for both amounts. The result is a
signed difference per line and an exact net balance. The request can retain a
planned payment date. Actual payment and recovery require separate evidence.
