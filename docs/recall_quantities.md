# Recall work, travel and payable quantities

`src.recall_quantities.quantify_recall` computes a quantity for one independently
eligible recall. A caller supplies actual work and actual outbound/return travel
as `timedelta` values, plus an explicit `RecallQuantityPolicy`. The selected
method is `cap_travel_sum_round_then_minimum_v1`:

1. Cap each actual journey independently at `travel_cap_each_way`.
2. Sum actual work and the two eligible journeys.
3. Round that total once to the nearest `rounding_quantum`, using explicitly
   selected `half_up` or `half_even` ties.
4. Apply the supplied minimum to the rounded total.

There are no default industrial values, rounding ties or inferred eligibility.
A minimum need not be a multiple of the rounding quantum: it is applied after
rounding, exactly as selected. Durations use integer microseconds; payable hours
are an exact `Fraction`. Negative travel/caps/minima, zero or negative work or
quantum, blank identities and unsupported methods are rejected. Zero caps and
zero minima are supported explicit choices.

For a synthetic policy with a 15-minute cap each way, a 15-minute quantum,
`half_up` ties and a two-hour minimum, 20 minutes of work plus journeys of
25 and five minutes gives 40 eligible minutes, 45 rounded minutes and 120 payable
minutes. The result still retains 20 worked minutes and the original journeys.
The minimum increment is 75 minutes; the rounding adjustment is five minutes.
A negative rounding adjustment is also possible, without changing actual time.

## Interaction and acceptance boundaries

Use the returned work evidence for actual-work history according to the qualified
overtime rule. Payable time includes other quantities and must not automatically
increment an overtime accumulator. `policy_id` identifies the caller's convention;
it is not a source-registry approval or instrument applicability assertion.

This method does not decide whether another recall earns a new minimum, how an
exclusion clock resets, whether a phone contact requires attendance, or whether
travel counts as work under another rule. It does not infer fixed per-contact
fees, calendar premiums, ordinary-time earnings or on-cost bases.

It also does not create a continuous time interval from the payable quantity.
Effective-dated pricing needs a separately qualified placement/allocation rule,
particularly across a rate or premium boundary. The existing anchored-window
planner is a different selected convention. Its minimum/grouping window must not
be substituted for an independent exclusion clock. Keep unresolved source and
interaction questions in the candidate layer when selecting the applicable rule.
