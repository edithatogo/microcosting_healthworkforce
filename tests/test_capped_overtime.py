# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Synthetic exact arithmetic for capped daily overtime and base interaction."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from fractions import Fraction

import pytest

from src.capped_overtime import (
    CappedDailyRule,
    DailyHistory,
    DailyTier,
    cost_capped_daily_overtime,
)
from src.conditions import ConditionRelease
from src.costing import Activity
from tests.checks import assert_that
from tests.test_conditions import condition
from tests.test_roster_costing import release


def rule(cap: str = "40") -> CappedDailyRule:
    """Create a fictional, source-linked daily tier schedule."""
    return CappedDailyRule(
        rule_id="daily",
        salary_cap_hourly=Decimal(cap),
        tiers=(
            DailyTier(starts_at_hours=Decimal(0), multiplier=Decimal("1.5")),
            DailyTier(starts_at_hours=Decimal(3), multiplier=Decimal(2)),
        ),
        source_id="synthetic-award-1",
        source_sha256="a" * 64,
        citation="synthetic clause",
        effective_from=date(2026, 1, 1),
        effective_to=date(2027, 1, 1),
        reviewed=True,
    )


def activity(hours: int = 4) -> Activity:
    """Return one synthetic overtime activity."""
    start = datetime(2026, 6, 2, 9, tzinfo=UTC)
    return Activity(
        activity_id="a",
        resource_id="worker",
        starts_at=start,
        ends_at=start + timedelta(hours=hours),
        resources=Decimal(1),
    )


def test_capped_tiers_adjust_already_counted_salary_once() -> None:
    """Four hours at capped 40 give 3*60+80 = 260, versus 200 base."""
    result = cost_capped_daily_overtime(
        release(),
        rule(),
        activity(),
        "UTC",
        DailyHistory(prior_hours=Decimal(0), complete=True),
    )
    assert_that(result.total == Fraction(260))
    assert_that(
        sum((x.adjustment for x in result.adjustments), Fraction(0)) == Fraction(60),
    )
    assert_that([x.hours for x in result.adjustments] == [Fraction(3), Fraction(1)])
    assert_that(result.base.activity_id == "a")


def test_signed_adjustment_and_prior_history() -> None:
    """A low cap can reduce a pre-counted base; prior hours select the tier."""
    result = cost_capped_daily_overtime(
        release(),
        rule("20"),
        activity(1),
        "UTC",
        DailyHistory(prior_hours=Decimal(3), complete=True),
    )
    assert_that(result.adjustments[0].adjustment == Fraction(-10))
    assert_that(result.total == Fraction(40))
    uncapped = cost_capped_daily_overtime(
        release(),
        rule("100"),
        activity(1),
        "UTC",
        DailyHistory(prior_hours=Decimal(0), complete=True),
    )
    assert_that(uncapped.total == Fraction(75))


def test_rejects_unqualified_history_date_and_source() -> None:
    """Incomplete history, overnight activity and mismatched sources fail closed."""
    with pytest.raises(ValueError, match="history"):
        cost_capped_daily_overtime(
            release(),
            rule(),
            activity(),
            "UTC",
            DailyHistory(prior_hours=Decimal(0), complete=False),
        )
    with pytest.raises(ValueError, match="source hash"):
        cost_capped_daily_overtime(
            release(),
            rule().model_copy(update={"source_sha256": "b" * 64}),
            activity(),
            "UTC",
            DailyHistory(prior_hours=Decimal(0), complete=True),
        )
    overnight = activity().model_copy(
        update={"ends_at": datetime(2026, 6, 3, 1, tzinfo=UTC)},
    )
    with pytest.raises(ValueError, match="calendar dates"):
        cost_capped_daily_overtime(
            release(),
            rule(),
            overnight,
            "UTC",
            DailyHistory(prior_hours=Decimal(0), complete=True),
        )


def test_split_at_tier_boundary_matches_whole_activity() -> None:
    """Explicit carry-over preserves the exact result when an activity is split."""
    whole = activity()
    first = whole.model_copy(update={"ends_at": whole.starts_at + timedelta(hours=2)})
    second = whole.model_copy(update={"starts_at": first.ends_at, "activity_id": "b"})
    full = cost_capped_daily_overtime(
        release(),
        rule(),
        whole,
        "UTC",
        DailyHistory(prior_hours=Decimal(0), complete=True),
    )
    left = cost_capped_daily_overtime(
        release(),
        rule(),
        first,
        "UTC",
        DailyHistory(prior_hours=Decimal(0), complete=True),
    )
    right = cost_capped_daily_overtime(
        release(),
        rule(),
        second,
        "UTC",
        DailyHistory(prior_hours=Decimal(2), complete=True),
    )
    assert_that(full.total == left.total + right.total)


def test_base_allowances_and_fractions_are_not_repriced_by_cap() -> None:
    """Only salary changes; retained base components are counted exactly once."""
    original = release()
    enriched = ConditionRelease.model_validate(
        {
            **original.model_dump(),
            "conditions": (
                *original.conditions,
                condition("allowance", "fixed_annual", "2000", "AUD/year"),
                condition("loading", "salary_fraction", "0.1", "fraction"),
            ),
        },
    )
    result = cost_capped_daily_overtime(
        enriched,
        rule(),
        activity(),
        "UTC",
        DailyHistory(prior_hours=Decimal(0), complete=True),
    )
    assert_that(result.total == Fraction(284))
    assert_that(result.base.segments[0].components["allowance"] == Decimal(4))
    assert_that(result.base.segments[0].components["loading"] == Decimal(20))


def test_outside_rule_period_and_unreviewed_rule_fail_closed() -> None:
    """A dated rule or review assertion cannot be extrapolated."""
    history = DailyHistory(prior_hours=Decimal(0), complete=True)
    with pytest.raises(ValueError, match="cover activity"):
        cost_capped_daily_overtime(
            release(),
            rule().model_copy(update={"effective_to": date(2026, 6, 2)}),
            activity(),
            "UTC",
            history,
        )
    with pytest.raises(ValueError, match="review"):
        cost_capped_daily_overtime(
            release(),
            rule().model_copy(update={"reviewed": False}),
            activity(),
            "UTC",
            history,
        )
