# Effective-dated derived components

A `DerivedSchedule` is an ordered sequence of required `RuleSeries`. Each
series has one component and one or more non-overlapping dated rule editions.
On each costing date the caller must supply exactly one covering edition per
series. Gaps, overlaps, duplicate identities and unavailable dependencies fail
closed. Ordering is explicit: a derived on-cost must follow the allowance it
uses as a base.

The snapshot and activity APIs reuse the existing condition and derived-rule
checks. Activities split at local-day boundaries; each row records the selected
rule and exact additive amount. The caller supplies source-backed effective
dates and eligibility. This does not infer industrial precedence, pay-period
rules, worker eligibility or intraday rule changes.
