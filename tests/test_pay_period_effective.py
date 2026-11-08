# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Synthetic first-full-period boundaries and source qualification."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from src.capped_overtime import DailyHistory, cost_capped_daily_overtime
from src.costing import Activity, cost_dynamic
from src.pay_period_effective import (
    FirstFullPeriodRule,
    PeriodCalendar,
    RetrospectiveAuthority,
    first_full_period,
)
from src.source_registry import SourceRegistry
from tests.checks import assert_that
from tests.test_capped_overtime import activity as overtime_activity
from tests.test_capped_overtime import rule as capped_rule
from tests.test_costing import release as flat_release
from tests.test_roster_costing import release
from tests.test_source_registry import source


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


def test_retrospective_authority_needs_reviewed_interval_and_known_date() -> None:
    """Later authority can cover earlier pay dates only with an explicit assertion."""
    later = source().model_copy(
        update={
            "effective_from": date(2024, 1, 26),
            "verified_through": date(2027, 1, 1),
        },
    )
    sources = SourceRegistry(records=(later,))
    period = PeriodCalendar(
        calendar_id="prior",
        boundaries=(
            datetime(2023, 5, 25, tzinfo=UTC),
            datetime(2023, 6, 8, tzinfo=UTC),
            datetime(2023, 6, 22, tzinfo=UTC),
        ),
        complete=True,
    )
    original = rule(datetime(2023, 6, 1, tzinfo=UTC))
    with pytest.raises(ValueError, match="coverage"):
        first_full_period(original, period, sources)
    authority = RetrospectiveAuthority(
        entitlement_from=date(2023, 6, 1),
        entitlement_to=date(2023, 7, 1),
        known_from=date(2024, 1, 26),
        as_known_at=date(2024, 2, 1),
        citation="synthetic retrospective clause",
        reviewed=True,
    )
    selected = first_full_period(
        original.model_copy(update={"retrospective": authority}),
        period,
        sources,
    )
    assert_that(selected.starts_at == datetime(2023, 6, 8, tzinfo=UTC))
    assert_that(selected.rule.retrospective == authority)
    with pytest.raises(ValueError, match="knowledge"):
        first_full_period(
            original.model_copy(
                update={
                    "retrospective": authority.model_copy(
                        update={"as_known_at": date(2024, 1, 25)},
                    ),
                },
            ),
            period,
            sources,
        )
    with pytest.raises(ValueError, match="interval"):
        first_full_period(
            original.model_copy(
                update={
                    "retrospective": authority.model_copy(
                        update={"entitlement_to": date(2023, 6, 8)},
                    ),
                },
            ),
            period,
            sources,
        )
    with pytest.raises(ValueError, match="review"):
        first_full_period(
            original.model_copy(
                update={
                    "retrospective": authority.model_copy(update={"reviewed": False}),
                },
            ),
            period,
            sources,
        )


def test_retrospective_authority_cannot_bypass_source_scope_or_hash() -> None:
    """Review cannot substitute a different employer or document edition."""
    history = RetrospectiveAuthority(
        entitlement_from=date(2026, 1, 1),
        entitlement_to=date(2026, 7, 1),
        known_from=date(2026, 6, 1),
        as_known_at=date(2026, 6, 3),
        citation="synthetic retrospective clause",
        reviewed=True,
    )
    base = rule(datetime(2026, 6, 3, tzinfo=UTC)).model_copy(
        update={"retrospective": history},
    )
    with pytest.raises(ValueError, match="coverage"):
        first_full_period(
            base.model_copy(update={"employer": "Other"}),
            calendar(),
            release().sources,
        )
    with pytest.raises(ValueError, match="hash"):
        first_full_period(
            base.model_copy(update={"source_sha256": "b" * 64}),
            calendar(),
            release().sources,
        )


def test_resolved_payroll_start_gates_new_overtime_ceiling() -> None:
    """The new ceiling starts at the resolved period, after the trigger date."""
    prices = release()
    resolved = first_full_period(
        rule(datetime(2026, 6, 3, tzinfo=UTC)),
        calendar(),
        prices.sources,
    )
    effective_day = resolved.starts_at.date()
    assert_that(effective_day == date(2026, 6, 15))
    ceiling = capped_rule().model_copy(update={"effective_from": effective_day})
    history = DailyHistory(prior_hours=Decimal(0), complete=True)
    start = resolved.starts_at
    shift = overtime_activity().model_copy(
        update={
            "starts_at": start,
            "ends_at": start + timedelta(hours=4),
        },
    )
    result = cost_capped_daily_overtime(prices, ceiling, shift, "UTC", history)
    assert_that(result.total == Decimal(260))
    preceding = shift.model_copy(
        update={
            "starts_at": start - timedelta(days=1),
            "ends_at": start - timedelta(days=1) + timedelta(hours=4),
        },
    )
    with pytest.raises(ValueError, match="cover"):
        cost_capped_daily_overtime(prices, ceiling, preceding, "UTC", history)
