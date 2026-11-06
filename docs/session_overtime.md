# Explicit session overtime on selected price components

`cost_session_overtime` takes a reviewed `CostRelease`, `WorkSession`,
`SessionOvertimeRule`, actual-work activities and an explicit rule timezone.
The session includes its identity, one resource/allocation, aware bounds, prior
eligible actual-work hours and the instant through which that history is complete.
The first supplied activity must start at that history boundary. All supplied
work must be inside the session, non-overlapping, and for one whole worker.
Prior hours cannot exceed elapsed time within the supplied session.

The rule declares its threshold, total multiplier, named premium components,
source/hash/citation, effective dates and review assertion. The engine prices
base components once through the dynamic ledger, then adds only the incremental
premium on the selected components above the cumulative work threshold. Every
selected component must exist in every used rate. This supports a qualified
loaded remuneration basis without guessing which components it includes.

For synthetic prices of 50/hour before noon and 70/hour afterwards, eight
prior hours and work from 11:00 to 13:00 under a nine-hour threshold and 1.6
total multiplier cost exactly 50 + 70*1.6 = 162 when both price components are
selected. Selecting salary alone gives a different explicit basis. Quantities,
premiums and total use exact fractions; the base component ledger retains its
rate/source lineage and the returned object retains the complete session/rule.

Midnight and gaps do not reset the caller-supplied session. Gaps do not count
as work. Splitting an activity preserves the exact result. Source and rule
coverage must include the entire work interval, including ordinary work.
Unreviewed rules, missing history/components, wrong workers or source hashes,
and uncovered intervals fail closed.

This method does not infer session membership, legal eligibility, loaded-rate
composition, recall guarantees, overtime/penalty stacking, employer on-cost
treatment, payroll rounding, annualisation or fortnightly cash processing.
Use actual eligible work rather than guaranteed paid intervals as history.
A hypothetical scenario requires explicit source and method assumptions; the
method is not a complete implementation of any industrial instrument.
