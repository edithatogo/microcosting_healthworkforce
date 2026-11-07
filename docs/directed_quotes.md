# Directed allowance exclusions

`src.directed_quotes.price_directed_quotes` prices a complete set of
pre-interaction eligibility facts for each supplied resource window. A reviewed
edge says that eligibility for one component excludes payment of another. Prices
do not determine priority: an eligible lower-priced trigger can exclude a larger
amount. Every unrelated survivor is added once. The result retains eligible
quotes, suppressed quotes, their direct blockers, paid quote identities and the
exact common price ledger, including a known all-negative zero case.

Create `DirectedQuoteRule(scope=..., exclusions=...)`, where `scope` is the shared
`ExclusiveQuoteRule` scope/window contract and each `QuoteExclusion` supplies a
trigger component, excluded component and citation within the scoped source.
The scope contract is reused for its source, date, unit and history checks; this
method does not choose one alternative from the entire group. Supply one
`DirectedQuoteCase` per nonoverlapping complete window, with one `QuoteEligibility`
for every declared component. Facts must describe eligibility before these
exclusions, with explicit known-positive or known-negative evidence. Eligible
facts require whole-window valid quotes even if their payment will be suppressed.

For example, a fictional rule `chokage -> fouled` pays chokage alone when both
pre-interaction predicates hold; it pays fouled when chokage is explicitly
ineligible and fouled is eligible. This models a declared "would otherwise be
payable" predicate, without proving an actual award's conditions or units.
If `A -> B` and `B -> C`, an eligible B still excludes C when A suppresses B's
payment. If B is ineligible, no inferred A-to-C edge is created. Every edge must
be explicit, distinct, non-self-referential and part of an acyclic graph. Circular
policies fail rather than silently eliminating every payment.

Quantities and complete windows are upstream facts or labelled assumptions. This
method uses one common quote unit and supplied quantity per case; it performs no
cross-unit conversion, per-fragment rounding, minimum calculation, paid-day
allocation, maximum comparison, payroll-calendar inference or rolling cap.
Split every relevant price or policy change into independently qualified windows;
do not split a single indivisible entitlement to evade whole-window checks.
Combining this with other selection methods requires a separately reviewed
ordering and component basis. It does not resolve asbestos exception names versus
letters or all-purposes versus no-penalty source wording.

A policy, exposure or component fact marked as an analyst assumption marks the
case's paid quantities and overall result as a scenario, even if that fact is
negative or suppressed. An entirely observed case remains observed when a
different case is hypothetical. Source scope/hash, knowledge dates, complete
history and eligibility evidence are revalidated, including nested frozen-model
copies. Exact rational quantities survive JSON round trips and low Decimal
precision. Static snapshots and dated windows share the same explicit pricing
function; a library result is not an industrial entitlement decision.
