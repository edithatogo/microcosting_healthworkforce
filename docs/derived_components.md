# Explicit component dependencies

`cost_derived_snapshot` and `cost_derived_activity` add reviewed, ordered
fractional rules to the existing condition-cost ledger. Each rule identifies
its own source, effective dates, fraction and named earlier component bases.
Names must be unique, and a missing or later dependency is rejected. The result
retains the base ledger and exact fractional amounts for each added rule and date.

For example, if an allowance is a reviewed fraction of salary and a separate
reviewed rule includes that allowance in an on-cost base, define the allowance
first and the incremental on-cost second. Do not add the full salary on-cost a
second time if it is already in the base ledger. The ACT health-professional
agreement's advanced-skill allowance illustrates a possible interaction, but
its eligibility, approval, applicable on-cost rate and source period must be
verified for the worker; the library does not infer them.

This method is additive. It does not infer entitlements, rule precedence,
thresholds, caps, payroll rounding or a rule for an uncovered date. Dynamic
costing validates each local-day segment; it does not automatically switch to
another rule edition when a rule stops applying.

## Retrospective derived rules

A derived rule may separately carry reviewed retrospective authority. Its
knowledge date must match the condition release, and its source hash and scope
are verified at the authority and knowledge dates. An earlier work date must
fall inside the rule's own reviewed entitlement interval. The salary's
retrospective authority does not automatically approve an allowance or on-cost.
This is a costing scenario and does not determine worker eligibility, legal
effect, backpay or cash timing.
