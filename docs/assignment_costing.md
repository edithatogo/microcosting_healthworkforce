# Explicit assignment timeline costing

`src.assignment_costing` prices declared classification/assignment changes for
one opaque subject using the existing annual-condition pricing functions.
`cost_assignment_snapshot(timeline, when, hours)` values explicit nominal hours
at an aware instant. `cost_assignment_activities(timeline, activities)` splits
elapsed activities at assignment boundaries, then uses each state's reviewed
condition release and local calendar. Ordinary wage/condition date changes
inside a state retain the existing daily condition splitting.

For synthetic hourly equivalents of $50 and $60, one hour in each declared class
costs $110. Two snapshot hours cost $100 before the transition and $120 at its
exclusive next-state start. No average rate replaces the transition.

## Declared states and decisions

An `AssignmentTimeline` requires a versioned identity, opaque subject ID,
knowledge date, explicit history-completeness assertion and a nonempty tuple of
ordered, contiguous, positive, bounded `AssignmentState` intervals. Each state
requires its own `ConditionRelease`, valid IANA timezone and decision ID/basis,
making date, knowledge date, input kind and reviewed assertion.

`decision_kind` is `observed_assignment` or `analyst_scenario`. References and
review flags are caller assertions; the library does not open evidence documents
or establish an employee's eligibility. Promotion, performance satisfaction,
Grading Committee approval and credited service must be resolved before declaring
an observed assignment. Source conditions remain subject to their normal
accepted-status, source-scope, hash, interval and retrospective-authority checks.

Knowledge cannot predate making. A state beginning on a local date before the
decision's making date requires `earlier_effect_reviewed=True`; otherwise it
fails. A timely decision learned later is a separate case. Both decision and
release knowledge, including source retrieval dates, must fit the run's cutoff.
These knowledge/making fields are date-grained; exact assignment effect is an
aware instant. No intraday approval convention or missing calendar is inferred.

```python
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from src.assignment_costing import (
    AssignmentState,
    AssignmentTimeline,
    cost_assignment_snapshot,
)
from src.conditions import ConditionRelease

# An independently qualified release for this declared classification.
release = ConditionRelease.model_validate_json(Path("reviewed-step.json").read_bytes())
state = AssignmentState(
    state_id="opaque-assignment-1",
    starts_at=datetime(2026, 6, 1, tzinfo=UTC),
    ends_at=datetime(2026, 7, 1, tzinfo=UTC),
    release=release,
    timezone="Australia/Brisbane",
    decision_id="opaque-reviewed-decision-1",
    decision_made_on=date(2026, 5, 1),
    decision_known_on=date(2026, 5, 2),
    earlier_effect_reviewed=False,
    decision_kind="analyst_scenario",
    decision_basis="Explicit scenario assignment; no real worker acceptance",
    decision_reviewed=True,
)
timeline = AssignmentTimeline(
    timeline_id="scenario-path-v1",
    subject_id="opaque-subject",
    as_known_on=date(2026, 6, 2),
    history_complete=True,
    states=(state,),
)
result = cost_assignment_snapshot(
    timeline,
    datetime(2026, 6, 2, tzinfo=UTC),
    Decimal("2"),
)
```

The supplied release must actually cover the requested local dates and be known
at the cutoff. Add contiguous states with their own decision evidence and
independently scoped releases for declared classification changes. Existing
`ConditionHistory` continues to model editions within one classification.

## Quantities, ledgers and replay

Activities must name the timeline subject and contain at most one resource.
Duplicate IDs, overlap for that subject and empty activity requests fail.
Explicit zero quantities still require state and price coverage throughout.
Changing employment FTE does not automatically multiply worked hours or an
already proportionate salary again; quantities and annual salary/paid-hours bases
remain explicit inputs with their own interpretation.

Results retain the validated complete timeline, original ordered activities or
snapshot instant, every state/decision/release pin, condition IDs and exact
rational hours/component amounts. Totals are `Fraction` values in AUD, aggregated
before any caller-selected rounding. Decimal projections in underlying condition
pricing do not become the aggregation oracle. Preserve the timeline SHA-256 with
the run; changing a source, decision, interval or knowledge assertion changes
that pin. Reusing a release ID for different content within a path fails.

A frozen earlier timeline can be replayed independently of a later decision
snapshot. The result is a nominal-hour valuation: historical cash paid, backpay,
settlement, productive capacity, overtime and source-specific progression rules
remain separate. No automatic FTE, month-length, payroll-cycle, approval or source
priority rule is added. This is a Python API; CLI defaults and PSA are unchanged.
