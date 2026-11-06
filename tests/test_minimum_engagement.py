# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Minimum engagement scenarios require explicit component selection."""

from datetime import UTC, date, datetime
from decimal import Decimal
from fractions import Fraction

import pytest

from src.conditions import ConditionRelease
from src.costing import Activity
from src.minimum_engagement import MinimumEngagementRule, cost_minimum_engagement
from src.source_registry import SourceRegistry
from tests.checks import assert_that
from tests.test_conditions import condition
from tests.test_source_registry import source


def example_release() -> ConditionRelease:
    """Build a synthetic salary and allowance release."""
    return ConditionRelease(
        release_id="example",
        jurisdiction="QLD",
        employer="Synthetic employer",
        classification="Synthetic grade",
        sources=SourceRegistry(records=(source(),)),
        conditions=(
            condition("salary", "salary", "100000", "AUD/year"),
            condition("hours", "paid_hours", "2000", "hours/year"),
            condition("allowance", "fixed_annual", "2000", "AUD/year"),
        ),
    )


def rule() -> MinimumEngagementRule:
    """Use a synthetic three-hour minimum applying to salary only."""
    return MinimumEngagementRule(
        rule_id="minimum",
        minimum_hours=Decimal(3),
        included_components=("salary",),
        source_id="synthetic-award-1",
        source_sha256="a" * 64,
        citation="synthetic clause",
        effective_from=date(2026, 1, 1),
        effective_to=date(2027, 1, 1),
        reviewed=True,
        eligibility_confirmed=True,
    )


def test_only_selected_components_are_paid_for_guaranteed_extra_time() -> None:
    """Two hours salary plus allowance, with one extra salary hour, total $152."""
    activity = Activity(
        activity_id="shift",
        resource_id="worker",
        starts_at=datetime(2026, 6, 2, 9, tzinfo=UTC),
        ends_at=datetime(2026, 6, 2, 11, tzinfo=UTC),
        resources=Decimal(1),
    )
    result = cost_minimum_engagement(example_release(), rule(), activity, "UTC")
    assert_that(result.worked_cost == Decimal(102))
    assert_that(result.minimum_increment == Decimal(50))
    assert_that(result.total == Decimal(152))


def test_unknown_components_and_unconfirmed_eligibility_fail() -> None:
    """Unsupported scope is rejected instead of applying a default."""
    activity = Activity(
        activity_id="shift",
        resource_id="worker",
        starts_at=datetime(2026, 6, 2, 9, tzinfo=UTC),
        ends_at=datetime(2026, 6, 2, 11, tzinfo=UTC),
        resources=Decimal(1),
    )
    with pytest.raises(ValueError, match="component"):
        cost_minimum_engagement(
            example_release(),
            rule().model_copy(update={"included_components": ("unknown",)}),
            activity,
            "UTC",
        )
    with pytest.raises(ValueError, match="eligibility"):
        cost_minimum_engagement(
            example_release(),
            rule().model_copy(update={"eligibility_confirmed": False}),
            activity,
            "UTC",
        )


def test_longer_activity_is_not_topped_up_and_cross_day_is_rejected() -> None:
    """No minimum applies beyond worked time, and date boundaries are explicit."""
    activity = Activity(
        activity_id="long",
        resource_id="worker",
        starts_at=datetime(2026, 6, 2, 9, tzinfo=UTC),
        ends_at=datetime(2026, 6, 2, 13, tzinfo=UTC),
        resources=Decimal(1),
    )
    result = cost_minimum_engagement(example_release(), rule(), activity, "UTC")
    assert_that(result.minimum_increment == Decimal(0))
    assert_that(result.total == Decimal(204))
    overnight = activity.model_copy(
        update={
            "starts_at": datetime(2026, 6, 2, 23, tzinfo=UTC),
            "ends_at": datetime(2026, 6, 3, 1, tzinfo=UTC),
        },
    )
    with pytest.raises(ValueError, match="calendar dates"):
        cost_minimum_engagement(example_release(), rule(), overnight, "UTC")


def test_minimum_engagement_retains_exact_fractional_worked_hours() -> None:
    """A one-hour salary-only minimum is exact after twenty minutes of work."""
    activity = Activity(
        activity_id="short",
        resource_id="worker",
        starts_at=datetime(2026, 6, 2, 9, tzinfo=UTC),
        ends_at=datetime(2026, 6, 2, 9, 20, tzinfo=UTC),
        resources=Decimal(1),
    )
    chosen = rule().model_copy(update={"minimum_hours": Decimal(1)})
    result = cost_minimum_engagement(example_release(), chosen, activity, "UTC")
    # Salary is paid for one hour and the hourly allowance for twenty minutes.
    assert_that(
        Fraction(result.exact_total_numerator, result.exact_total_denominator)
        == Fraction(151, 3),
    )
