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
