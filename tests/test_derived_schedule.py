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
from tests.test_retrospective_conditions import retrospective_release


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


def test_schedule_revalidates_and_rejects_unordered_dependencies() -> None:
    """Copied malformed schedules and forward dependencies do not execute."""
    series = schedule().series[0]
    old, new = series.editions
    repeated = new.model_copy(update={"rule_id": old.rule_id})
    with pytest.raises(ValueError, match="Duplicate derived rule identity"):
        RuleSeries(component="allowance", editions=(old, repeated))
    overlap = new.model_copy(update={"effective_from": date(2026, 6, 2)})
    changed = series.model_copy(update={"editions": (old, overlap)})
    copied = schedule().model_copy(update={"series": (changed,)})
    with pytest.raises(ValueError, match="overlap"):
        copied.select(date(2026, 6, 2))
    oncost = rule("oncost", "allowance_super", ("allowance",), "0.1")
    reversed_order = DerivedSchedule(
        series=(RuleSeries(component="allowance_super", editions=(oncost,)), series),
    )
    with pytest.raises(ValueError, match="missing or not yet"):
        cost_scheduled_snapshot(
            baseline(),
            date(2026, 6, 2),
            Decimal(1),
            reversed_order,
        )


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


def test_schedule_composes_with_reviewed_retrospective_rules() -> None:
    """A change across two historical days requires each rule's own authority."""
    release = retrospective_release()
    authority = release.conditions[0].retrospective
    if authority is None:
        msg = "Test requires retrospective authority"
        raise ValueError(msg)
    old = rule("old", "allowance", ("salary",), "0.05").model_copy(
        update={
            "effective_from": date(2025, 6, 1),
            "effective_to": date(2025, 7, 2),
            "retrospective": authority,
        },
    )
    new = rule("new", "allowance", ("salary",), "0.10").model_copy(
        update={
            "effective_from": date(2025, 7, 2),
            "effective_to": date(2026, 1, 1),
            "retrospective": authority,
        },
    )
    dated = DerivedSchedule(
        series=(RuleSeries(component="allowance", editions=(old, new)),),
    )
    start = datetime(2025, 7, 1, 23, tzinfo=UTC)
    activity = Activity(
        activity_id="historical",
        resource_id="worker",
        starts_at=start,
        ends_at=start + timedelta(hours=2),
        resources=Decimal(1),
    )
    result = cost_scheduled_activity(release, activity, "UTC", dated)
    assert_that(result.exact_total == Fraction(215, 2))
    assert_that([row.rule.rule_id for row in result.rows] == ["old", "new"])
    missing = new.model_copy(update={"retrospective": None})
    unreviewed = DerivedSchedule(
        series=(RuleSeries(component="allowance", editions=(old, missing)),),
    )
    with pytest.raises(ValueError, match="scope"):
        cost_scheduled_activity(release, activity, "UTC", unreviewed)


@pytest.mark.parametrize(
    ("start", "end", "elapsed_hours"),
    [
        (
            datetime(2026, 4, 4, 13, tzinfo=UTC),
            datetime(2026, 4, 5, 14, tzinfo=UTC),
            25,
        ),
        (
            datetime(2026, 10, 3, 14, tzinfo=UTC),
            datetime(2026, 10, 4, 13, tzinfo=UTC),
            23,
        ),
    ],
)
def test_local_daylight_transition_uses_elapsed_hours(
    start: datetime,
    end: datetime,
    elapsed_hours: int,
) -> None:
    """A full Sydney local day costs its actual 23 or 25 elapsed hours."""
    activity = Activity(
        activity_id="daylight-transition",
        resource_id="worker",
        starts_at=start,
        ends_at=end,
        resources=Decimal(1),
    )
    constant = DerivedSchedule(
        series=(
            RuleSeries(
                component="allowance",
                editions=(rule("daylight", "allowance", ("salary",), "0.05"),),
            ),
        ),
    )
    result = cost_scheduled_activity(baseline(), activity, "Australia/Sydney", constant)
    assert_that(result.exact_total == Fraction(115, 2) * elapsed_hours)
    assert_that(len(result.rows) == 1)
    assert_that(result.rows[0].quantity_hours == Fraction(elapsed_hours))
