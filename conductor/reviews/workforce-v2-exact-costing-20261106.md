# Workforce exact-costing continuation — 6 November 2026

Source commits `00db1e5` and `d266c98` extend exact rational totals to cumulative
overtime, nondecreasing overtime tiers, single-day minimum engagements and
paid-capacity scenarios. Capacity results also expose an exact productive-hour
rate. The separate `flat_hourly_v1` snapshot/activity API lacked exact totals at that
checkpoint; source commit `073c3d3` subsequently adds them and revalidates
resource/activity inputs so model copies cannot bypass nonnegative checks. These are additive numerator/denominator fields: existing Decimal results
remain available and may retain context-precision differences. Exact amounts use
the original Decimal input values and elapsed microseconds, with no implicit
currency rounding. They do not validate a caller's input, applicability,
review assertion or industrial-rule interpretation beyond the existing contracts.

Synthetic threshold tests compare a one-hour shift with three consecutive
20-minute activities and require equal exact totals for both single- and
two-tier overtime. Additional tests verify a 20-minute minimum-engagement
calculation and a nonterminating productive-hour ratio. Focused tests and full
`make ci` passed on Python 3.15.2 with 139 tests, Ruff formatting/lint, strict
type checking and Bandit. The full CI output is retained privately at
`.private-runs/workbook-source-inventory/ci-exact-final.log`.

The source-backed Victorian grade comparison and remaining historical archive
conflicts are recorded in [the source/parity review](./workforce-v2-source-and-parity-20261106.md).
No change was made to the original workbook or legacy model. Cost-rule interaction,
calendar/holiday rules, current and historical source applicability, and candidate
semantic acceptance remain open. Both tracks remain in progress.

The final full `make ci` check for `073c3d3` passed with 142 tests, Ruff, strict
type checking and Bandit on Python 3.15.2. Exact flat-rate tests cover static/
dynamic agreement and invariance under fractional-hour segmentation. Decimal
fields remain context-precision results; explicit rational fields support exact
aggregation before caller-selected rounding.
