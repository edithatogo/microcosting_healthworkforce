# Minimum engagement and overtime interaction — 6 November 2026

The current functions calculate distinct scenarios. `cost_minimum_engagement`
returns worked base cost plus the guaranteed-hours increment;
`cost_overtime_period` returns worked base cost plus salary-only overtime
increment. Their totals cannot be added: each includes the worked base.

For a synthetic example, assume one hour worked at $50 salary per hour, a
three-hour salary-only minimum, and a 1.5 overtime multiplier applying to all
worked time. The minimum method returns $150 ($50 base plus $100 minimum
increment); the overtime method returns $75 ($50 base plus $25 overtime
increment). Adding their totals produces $225 and double-counts the $50 base.
If the explicitly selected interaction applies overtime only to the worked hour
and pays the minimum top-up at ordinary salary rate, the combined answer is
$175: base $50, overtime increment $25 and minimum increment $100. This is a
synthetic policy example, not an interpretation of an award.

An alternative instrument might count guaranteed but unworked hours towards the
overtime threshold, or apply overtime to the guaranteed hours. Those choices,
component inclusion, pay-period history, stacking and pay-effective dates need
explicit source-backed rules; the existing APIs do not establish them. A
combined API should require a declared interaction, preserve exact rational
components and identify the source and rule for every increment. It must not
sum standalone totals or silently infer a rule. Test boundaries should include
threshold crossings, non-salary components, adjacent segmentation and date
transitions, with unsupported combinations rejected.

## Implementation continuation

Source commits `232edfe` and `6752a03` implement the selected synthetic method
in the isolated `codex/workforce-interaction` lane. The caller must supply a
separate reviewed and dated interaction citation and source hash, which are
checked against the release scope; the result retains all three rule citations.
The full local suite passed 152 tests on Python 3.15.2; Ruff, strict basedpyright
and Bandit passed. This used the existing qualified dependency environment for
checks. A source distribution and wheel built and the wheel imported outside the
checkout; this is not a full clean installed-package behavioral test. Gitleaks
and reviewed Presidio scanned all outgoing blobs. [PR #49](https://github.com/edithatogo/microcosting_healthworkforce/pull/49)
passed its exact-head checks and merged as `009dad2`; receiving-main CI and
Security passed on that merge. The source worktree and local branch were retired
after preserving the private privacy receipt; the remote branch was absent.

This remains a bounded calculation, not an accepted industrial entitlement.
Other treatments, real source qualification, additional interaction families,
semantic mapping and acquisition work remain open.
