# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Synthetic first-full-period boundaries and source qualification."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from src.costing import Activity, cost_dynamic
from src.pay_period_effective import (
    FirstFullPeriodRule,
    PeriodCalendar,
    first_full_period,
)
from tests.checks import assert_that
from tests.test_costing import release as flat_release
from tests.test_roster_costing import release


def rule(trigger: datetime) -> FirstFullPeriodRule:
    """Create a synthetic explicitly reviewed commencement rule."""
    return FirstFullPeriodRule(
        rule_id="first-full",
        jurisdiction="QLD",
        employer="Synthetic employer",
        classification="Synthetic grade",
        timezone="Australia/Brisbane",
        trigger_at=trigger,
        source_id="synthetic-award-1",
        source_sha256="a" * 64,
        citation="synthetic pay period clause",
        reviewed=True,
    )


def calendar() -> PeriodCalendar:
    """Provide three known consecutive synthetic pay-period boundaries."""
    return PeriodCalendar(
        calendar_id="synthetic-payroll",
        boundaries=tuple(datetime(2026, 6, day, tzinfo=UTC) for day in (1, 15, 29)),
        complete=True,
    )


def test_first_full_period_inclusive_and_between_boundaries() -> None:
    """A date inside a period waits for the next supplied complete period."""
    sources = release().sources
    at_boundary = first_full_period(
        rule(datetime(2026, 6, 1, tzinfo=UTC)),
        calendar(),
        sources,
    )
    mid_period = first_full_period(
        rule(datetime(2026, 6, 3, tzinfo=UTC)),
        calendar(),
        sources,
    )
    assert_that(at_boundary.starts_at == calendar().boundaries[0])
    assert_that(mid_period.starts_at == calendar().boundaries[1])
    assert_that(mid_period.ends_at == calendar().boundaries[2])
    assert_that(mid_period.calendar.calendar_id == "synthetic-payroll")


def test_missing_history_or_future_period_is_rejected() -> None:
    """A truncated calendar cannot silently choose a later boundary."""
    sources = release().sources
    with pytest.raises(ValueError, match="at or before"):
        first_full_period(rule(datetime(2026, 5, 31, tzinfo=UTC)), calendar(), sources)
    with pytest.raises(ValueError, match="next complete"):
        first_full_period(rule(datetime(2026, 6, 29, tzinfo=UTC)), calendar(), sources)
    with pytest.raises(ValueError, match="complete"):
        first_full_period(
            rule(datetime(2026, 6, 3, tzinfo=UTC)),
            calendar().model_copy(update={"complete": False}),
            sources,
        )


def test_rule_source_scope_and_review_are_checked() -> None:
    """Review and the precise source edition cannot be substituted."""
    sources = release().sources
    r = rule(datetime(2026, 6, 3, tzinfo=UTC))
    with pytest.raises(ValueError, match="hash"):
        first_full_period(
            r.model_copy(update={"source_sha256": "b" * 64}),
            calendar(),
            sources,
        )
    with pytest.raises(ValueError, match="coverage"):
        first_full_period(
            r.model_copy(update={"classification": "Other"}),
            calendar(),
            sources,
        )
    with pytest.raises(ValueError, match="review"):
        first_full_period(r.model_copy(update={"reviewed": False}), calendar(), sources)


def test_resolved_boundary_drives_dynamic_rate_transition() -> None:
    """A resolved boundary splits a shift without pricing the increase early."""
    current = flat_release()
    period = first_full_period(
        rule(datetime(2026, 6, 3, tzinfo=UTC)),
        calendar(),
        current.sources,
    )
    change = period.starts_at
    before = current.rates[0].model_copy(
        update={"starts_at": change - timedelta(days=14), "ends_at": change},
    )
    after = current.rates[1].model_copy(update={"starts_at": change, "ends_at": None})
    selected = current.model_copy(update={"rates": (before, after)})
    activity = Activity(
        activity_id="shift",
        resource_id="staff",
        starts_at=change - timedelta(hours=1),
        ends_at=change + timedelta(hours=1),
        resources=Decimal(1),
    )
    result = cost_dynamic(selected, (activity,))
    assert_that(result.total == Decimal(120))
    assert_that([row.starts_at for row in result.rows] == [activity.starts_at, change])
