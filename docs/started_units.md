# Grouped started-unit allowances

`price_started_units` in `src.started_units` sums declared exposure intervals and
rounds up once per explicitly reviewed group. A positive fraction of a quantum
costs one unit; an exact boundary does not add another. Physical exposure,
payable units and the ceiling increment remain separate in the result. The
increment does not invent worked or rostered time.

The rule requires a positive timedelta quantum, component/unit, reviewed grouping
and elapsed-time interpretation, timezone, source/hash/citation, scope and
operative/knowledge dates. `ceil_grouped_elapsed_units_v1` measures exact UTC
microseconds. Review both the quantum-to-price-unit relationship and grouping;
the library does not decide whether fragments belong to a shift, day or episode.
Policy assumptions remain labelled scenarios.

Each complete eligible window declares its resource/identity, positive aware
start/end, valuation date, chosen quote and dated evidence. Its exposure intervals
must have unique identities, positive aware instants, no overlap and full window
containment. Gaps do not count. Adjacent fragments sum before a single ceiling;
splitting identical exposure into fragments does not multiply payments.

Empty intervals require `no_exposure_confirmed=True`; nonempty intervals require
it false. Unknown history/eligibility and an empty window set fail. A known zero
still requires policy/source/price coverage and retains a zero-priced row.
Duplicate or overlapping resource windows are rejected within the supplied call.
Observed evidence cannot predate the completed window or exceed the knowledge
date. Inputs modified through unchecked copies are revalidated at every level.

Both local-date endpoints must be covered by the policy source and selected quote.
Prices must match component/unit and policy scope/knowledge. A group spanning a
price change fails: allocation of a rounded quantum across changing rates needs
an explicit source-qualified method. Arbitrarily splitting that group and
rounding each part can overpay and is not an automatic remedy.

One window supports snapshot pricing; several dated groups support dynamic
pricing. There is no default annualisation, wall-clock/roster-hour conversion,
minimum guarantee, rolling cap, geographical/cohort inference, cross-call
history check or automatic combination with salary/on-costs. Public tests use
fictional policy and prices. Actual worker eligibility, source exceptions and
grouping interpretation require separate qualification.
