# Anchored recall window planning

`plan_recall_windows` requires an explicit `anchored_first_recall_v1` selection,
a positive minimum duration and timestamped evidence for one opaque allocation.
A recall starting strictly before the first event's minimum ends joins that
window. An event at the boundary starts another window. A later contact does
not reset the anchor. Work extending beyond the minimum extends the planned
payable interval. Worked and payable microseconds are retained separately,
along with the original events, using UTC elapsed time.

For example, work at minutes 0–5 and 25–35 under a 30-minute window records
15 worked minutes and a 35-minute planned interval. Empty evidence yields no
windows; duplicate IDs, overlapping work, naive/nonpositive intervals and
multiple allocations fail. This method requires qualification against the
selected source's grouping interpretation and complete event evidence. It does
not establish employee eligibility, entitlement, loaded rates, multipliers,
rounding, payroll payment or integration with cumulative overtime.

## Effective-dated pricing

`cost_recall_windows` accepts an explicit `CostRelease`, resource identity,
events, minimum and grouping method. It prices each planned interval from its
start through its paid end using `cost_dynamic`. The returned `RecallCost`
retains both the original worked events and the component/rate/source ledger,
with pricing method `anchored_window_flat_rate_v1`. Rates must already include
any qualified loading or component composition; this adapter derives neither
a recall multiplier nor legal eligibility.

For example, a 30-minute guarantee starting at 11:50, priced at 50/hour before
noon and 70/hour afterwards, costs exactly 95/3 currency units. Actual calls
lasting five minutes at 11:50 and five minutes at 12:05 remain ten minutes of
work. All 30 guaranteed minutes require rate coverage, even when the actual
calls fit within a shorter covered interval. Rate changes split the pricing
ledger. Empty event evidence creates no windows or charges.

The adapter supplies planned flat-rate guarantee costing. Combining guarantees
with work-based cumulative overtime, source-specific eligibility, payroll
rounding or separately payable overlapping duties requires explicit rule
qualification; guarantee time must not silently become overtime work history.
