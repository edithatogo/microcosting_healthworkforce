# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Effective-dated derived rule selection across static and dynamic costs."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from fractions import Fraction

import pytest

from src.costing import Activity
from src.derived_schedule import (
    DerivedSchedule,
    RuleSeries,
    cost_scheduled_activity,
    cost_scheduled_snapshot,
)
from tests.checks import assert_that
from tests.test_derived_components import baseline, rule


def schedule() -> DerivedSchedule:
    """Change a reviewed allowance from five to ten percent at midnight."""
    old = rule("old", "allowance", ("salary",), "0.05").model_copy(
        update={"effective_to": date(2026, 6, 3)},
    )
    new = rule("new", "allowance", ("salary",), "0.10").model_copy(
        update={"effective_from": date(2026, 6, 3)},
    )
    return DerivedSchedule(
        series=(RuleSeries(component="allowance", editions=(old, new)),),
    )


def test_shift_changes_rule_at_date_and_matches_snapshots() -> None:
    """The change applies per local day and exact results add without duplication."""
    start = datetime(2026, 6, 2, 23, tzinfo=UTC)
    activity = Activity(
        activity_id="overnight",
        resource_id="worker",
        starts_at=start,
        ends_at=start + timedelta(hours=2),
        resources=Decimal(1),
    )
    dynamic = cost_scheduled_activity(baseline(), activity, "UTC", schedule())
    first = cost_scheduled_snapshot(
        baseline(),
        date(2026, 6, 2),
        Decimal(1),
        schedule(),
    )
    second = cost_scheduled_snapshot(
        baseline(),
        date(2026, 6, 3),
        Decimal(1),
        schedule(),
    )
    assert_that(
        dynamic.exact_total
        == first.exact_total + second.exact_total
        == Fraction(235, 2),
    )
    assert_that([r.rule.rule_id for r in dynamic.rows] == ["old", "new"])


def test_gap_overlap_and_wrong_scope_fail_closed() -> None:
    """No missing, overlapping or incorrectly sourced rule is selected."""
    existing = schedule().series[0].editions
    overlap = existing[1].model_copy(update={"effective_from": date(2026, 6, 2)})
    with pytest.raises(ValueError, match="overlap"):
        RuleSeries(component="allowance", editions=(existing[0], overlap))
    gap = existing[1].model_copy(update={"effective_from": date(2026, 6, 4)})
    incomplete = DerivedSchedule(
        series=(RuleSeries(component="allowance", editions=(existing[0], gap)),),
    )
    with pytest.raises(ValueError, match="lacks one rule"):
        cost_scheduled_snapshot(baseline(), date(2026, 6, 3), Decimal(1), incomplete)
    bad = existing[0].model_copy(update={"source_sha256": "b" * 64})
    altered = DerivedSchedule(
        series=(RuleSeries(component="allowance", editions=(bad, existing[1])),),
    )
    with pytest.raises(ValueError, match="hash"):
        cost_scheduled_snapshot(baseline(), date(2026, 6, 2), Decimal(1), altered)


def test_ordered_dependency_uses_each_selected_allowance() -> None:
    """An incremental on-cost tracks changing allowance rather than salary twice."""
    oncost = rule("oncost", "allowance_super", ("allowance",), "0.1")
    with_oncost = DerivedSchedule(
        series=(
            *schedule().series,
            RuleSeries(component="allowance_super", editions=(oncost,)),
        ),
    )
    start = datetime(2026, 6, 2, 23, tzinfo=UTC)
    activity = Activity(
        activity_id="overnight",
        resource_id="worker",
        starts_at=start,
        ends_at=start + timedelta(hours=2),
        resources=Decimal(1),
    )
    result = cost_scheduled_activity(baseline(), activity, "UTC", with_oncost)
    assert_that(
        [row.amount for row in result.rows]
        == [Fraction(5, 2), Fraction(1, 4), Fraction(5), Fraction(1, 2)],
    )
    assert_that(result.exact_total == Fraction(473, 4))


def test_subsecond_activity_retains_exact_rational_total() -> None:
    """No rounded decimal duration is used as the exact-cost quantity."""
    start = datetime(2026, 6, 2, 9, tzinfo=UTC)
    activity = Activity(
        activity_id="instant",
        resource_id="worker",
        starts_at=start,
        ends_at=start + timedelta(microseconds=1),
        resources=Decimal(1),
    )
    result = cost_scheduled_activity(baseline(), activity, "UTC", schedule())
    assert_that(result.exact_total == Fraction(115, 7200000000))
