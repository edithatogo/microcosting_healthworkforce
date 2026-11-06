# Highest comparable quoted allowances

`price_highest_quotes` in `src.highest_quotes` pays one maximum rate per explicitly
qualified exposure window. The same API supports snapshots and dated windows.
It preserves eligible losing prices, every tied winning quote ID and one
lexicographically selected paid ID. Ties do not produce multiple payments.

`HighestQuoteRule` contains a source-qualified `ExclusiveQuoteRule`, explicit
comparability review and its basis. The group must represent comparable
alternatives with one common unit; matching numbers or labels do not establish
that different disabilities are of substantially the same nature.

Each `HighestQuoteCase` contains a `QuoteExposureWindow` and exactly one
`QuoteEligibility` fact per declared component. Facts require an explicit boolean,
basis, evidence identity/hash/date and observed/assumed status. An eligible fact
names its source-qualified quote; a negative fact must omit a quote. Unknown,
omitted, duplicate or unpriced eligible alternatives fail rather than shrinking
the comparison. A complete all-negative set produces a retained zero selection
and no payment row. An empty or unqualified exposure set fails.

The shared window validator checks source hash/scope/knowledge and both local-date
endpoints, complete eligible history, resource identity, uniqueness and non-overlap.
All eligible quotes, including losers, must match the component/unit and cover
the entire window. Split relevant rate changes explicitly. Quantities remain
caller-supplied Decimal or Fraction values; exact pricing uses `price_units`.
No conversion, annualisation or proration is inferred. Observed facts must not
predate the complete window or exceed the policy knowledge date. Assumptions
propagate to the result and their own payment row without relabelling other
observed rows.

Comparability, cohort eligibility, disability assessment, window allocation,
quantity rounding, source precedence and salary/overtime bases remain reviewed
inputs. The API computes a maximum per window; it does not substitute for a
whole-period higher-of rule, rolling 24-hour cap, minimum engagement, incremental
height/scaffold interpretation or cross-call duplicate detection. It does not
combine the winning allowance with salary, taxes or employer on-cost ledgers.
Public tests use fictional prices and source assertions.
