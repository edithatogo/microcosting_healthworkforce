# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Session thresholds use actual work and explicit loaded-rate components."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from fractions import Fraction
from zoneinfo import ZoneInfo

import pytest

from src.costing import Activity
from src.session_overtime import (
    SessionOvertimeRule,
    WorkSession,
    cost_session_overtime,
)
from tests.checks import assert_that
from tests.test_costing import release


def rule() -> SessionOvertimeRule:
    """Build a synthetic reviewed multiplier on both supplied price components."""
    return SessionOvertimeRule(
        rule_id="session-test",
        threshold_hours=Decimal(9),
        multiplier=Decimal("1.6"),
        premium_components=("salary", "on_cost"),
        source_id="synthetic-award-1",
        source_sha256="a" * 64,
        citation="Synthetic clause",
        effective_from=date(2026, 1, 1),
        effective_to=date(2027, 1, 1),
        reviewed=True,
    )


def session(start: datetime, prior: Decimal = Decimal(0)) -> WorkSession:
    """Supply a complete explicit history and bounds for one worker session."""
    return WorkSession(
        session_id="session-a",
        resource_id="staff",
        allocation_id="worker",
        starts_at=start - timedelta(hours=8),
        ends_at=start + timedelta(hours=3),
        prior_hours=prior,
        history_through=start,
        history_complete=True,
    )


def activity(start: datetime, hours: int = 2) -> Activity:
    """One actual-work interval, without minimum or guarantee quantities."""
    return Activity(
        activity_id="work",
        resource_id="staff",
        allocation_id="worker",
        starts_at=start,
        ends_at=start + timedelta(hours=hours),
        resources=Decimal(1),
    )


def test_session_threshold_and_rate_change_price_loaded_components() -> None:
    """Eight prior hours plus two current: 50 + 70*1.6 = 162."""
    start = datetime(2026, 1, 1, 11, tzinfo=UTC)
    result = cost_session_overtime(
        release(),
        session(start, Decimal(8)),
        rule(),
        (activity(start),),
        "UTC",
    )
    expected = Fraction(162)
    assert_that(result.total == expected)
    assert_that(sum((row.overtime_hours for row in result.rows), Fraction()) == 1)
    assert_that([row.rate_id for row in result.rows] == ["morning", "afternoon"])
    assert_that(result.rule.premium_components == ("salary", "on_cost"))
    assert_that(result.base.release_id == "synthetic-1")


def test_midnight_does_not_reset_a_supplied_session() -> None:
    """Half an hour at 70 then half at 112 costs 91 across midnight."""
    start = datetime(2026, 1, 1, 23, 30, tzinfo=UTC)
    selected = rule().model_copy(update={"threshold_hours": Decimal("0.5")})
    result = cost_session_overtime(
        release(),
        session(start),
        selected,
        (activity(start, 1),),
        "UTC",
    )
    expected = Fraction(91)
    assert_that(result.total == expected)


def test_selected_components_and_activity_splitting_preserve_exact_cost() -> None:
    """Only named components receive a premium; splitting does not reset history."""
    start = datetime(2026, 1, 1, 11, tzinfo=UTC)
    selected = rule().model_copy(update={"premium_components": ("salary",)})
    whole = activity(start)
    parts = (
        whole.model_copy(update={"ends_at": start + timedelta(minutes=30)}),
        whole.model_copy(
            update={
                "activity_id": "rest",
                "starts_at": start + timedelta(minutes=30),
            },
        ),
    )
    original = cost_session_overtime(
        release(),
        session(start, Decimal(8)),
        selected,
        (whole,),
        "UTC",
    )
    split = cost_session_overtime(
        release(),
        session(start, Decimal(8)),
        selected,
        parts,
        "UTC",
    )
    expected = Fraction(156)
    assert_that(original.total == split.total == expected)


def test_missing_history_scope_or_price_components_fail() -> None:
    """A supplied session cannot hide incomplete history or different workers."""
    start = datetime(2026, 1, 1, 11, tzinfo=UTC)
    period = session(start)
    with pytest.raises(ValueError, match="history"):
        cost_session_overtime(
            release(),
            period.model_copy(update={"history_complete": False}),
            rule(),
            (activity(start),),
            "UTC",
        )
    with pytest.raises(ValueError, match="allocation"):
        cost_session_overtime(
            release(),
            period,
            rule(),
            (activity(start).model_copy(update={"allocation_id": "other"}),),
            "UTC",
        )
    with pytest.raises(ValueError, match="component"):
        cost_session_overtime(
            release(),
            period,
            rule().model_copy(update={"premium_components": ("absent",)}),
            (activity(start),),
            "UTC",
        )


def test_rule_must_cover_entire_work_interval() -> None:
    """Starting inside a rule does not permit work beyond its exclusive expiry."""
    start = datetime(2026, 1, 1, 23, 30, tzinfo=UTC)
    selected = rule().model_copy(update={"effective_to": date(2026, 1, 2)})
    with pytest.raises(ValueError, match="cover"):
        cost_session_overtime(
            release(),
            session(start),
            selected,
            (activity(start, 1),),
            "UTC",
        )


def test_gaps_do_not_count_as_work_and_ordinary_cost_reduces_to_base() -> None:
    """An unpaid gap does not advance the threshold or reset the session."""
    start = datetime(2026, 1, 1, 11, tzinfo=UTC)
    items = (
        activity(start, 1),
        activity(start + timedelta(hours=2), 1).model_copy(
            update={"activity_id": "later"},
        ),
    )
    result = cost_session_overtime(
        release(),
        session(start, Decimal(8)),
        rule(),
        items,
        "UTC",
    )
    expected = Fraction(162)
    expected_hours = Fraction(10)
    assert_that(result.total == expected)
    assert_that(result.cumulative_hours == expected_hours)
    ordinary = cost_session_overtime(
        release(),
        session(start),
        rule(),
        (activity(start),),
        "UTC",
    )
    assert_that(
        ordinary.total
        == Fraction(
            ordinary.base.exact_total_numerator,
            ordinary.base.exact_total_denominator,
        ),
    )


def test_invalid_history_rule_and_overlapping_work_fail_closed() -> None:
    """Reject impossible history, bad provenance, missing review and duplicate work."""
    start = datetime(2026, 1, 1, 11, tzinfo=UTC)
    with pytest.raises(ValueError, match="history"):
        session(start, Decimal(9))
    with pytest.raises(ValueError, match="hash"):
        cost_session_overtime(
            release(),
            session(start),
            rule().model_copy(
                update={"source_sha256": "b" * 64},
            ),
            (activity(start),),
            "UTC",
        )
    with pytest.raises(ValueError, match="review"):
        cost_session_overtime(
            release(),
            session(start),
            rule().model_copy(
                update={"reviewed": False},
            ),
            (activity(start),),
            "UTC",
        )
    with pytest.raises(ValueError, match="overlap"):
        cost_session_overtime(
            release(),
            session(start),
            rule(),
            (
                activity(start),
                activity(start).model_copy(
                    update={"activity_id": "duplicate-work"},
                ),
            ),
            "UTC",
        )


@pytest.mark.parametrize(
    ("month", "day", "expected"),
    [(10, 4, Fraction(91)), (4, 5, Fraction(315))],
)
def test_session_threshold_uses_elapsed_time_across_sydney_dst(
    month: int,
    day: int,
    expected: Fraction,
) -> None:
    """Two wall-clock hours span one spring hour or three autumn hours."""
    zone = ZoneInfo("Australia/Sydney")
    start = datetime(2026, month, day, 1, 30, tzinfo=zone)
    stop = datetime(2026, month, day, 3, 30, tzinfo=zone)
    work = activity(start).model_copy(update={"ends_at": stop})
    selected = rule().model_copy(update={"threshold_hours": Decimal("0.5")})
    result = cost_session_overtime(
        release(),
        session(start),
        selected,
        (work,),
        "Australia/Sydney",
    )
    assert_that(result.total == expected)
