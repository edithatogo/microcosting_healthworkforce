# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Synthetic explicit minimum and overtime interaction."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from fractions import Fraction

import pytest
from pydantic import ValidationError

from src.costing import Activity
from src.rule_interaction import InteractionRules, cost_minimum_with_overtime
from tests.checks import assert_that
from tests.test_minimum_engagement import rule as minimum_rule
from tests.test_roster_costing import period, release
from tests.test_roster_costing import rule as overtime_rule


def test_minimum_and_overtime_do_not_double_count_base() -> None:
    """A three-hour minimum and one overtime hour total $175, not $225."""
    start = datetime(2026, 6, 2, 9, tzinfo=UTC)
    activity = Activity(
        activity_id="shift",
        resource_id="worker",
        starts_at=start,
        ends_at=start + timedelta(hours=1),
        resources=Decimal(1),
    )
    overtime = overtime_rule().model_copy(update={"threshold_hours": Decimal(0)})
    result = cost_minimum_with_overtime(
        release(),
        period(),
        InteractionRules(
            method="worked_overtime_ordinary_minimum_v1",
            minimum=minimum_rule(),
            overtime=overtime,
            rule_id="interaction",
            source_id="synthetic-award-1",
            source_sha256="a" * 64,
            citation="synthetic interaction clause",
            effective_from=date(2026, 1, 1),
            effective_to=date(2027, 1, 1),
            reviewed=True,
        ),
        activity,
        "UTC",
    )
    assert_that(
        Fraction(result.exact_total_numerator, result.exact_total_denominator)
        == Fraction(175),
    )
    assert_that(result.minimum_source_sha256 == minimum_rule().source_sha256)
    assert_that(result.overtime_citation == overtime.citation)


def test_unrecognised_interaction_is_rejected() -> None:
    """No other treatment of minimum and overtime is silently inferred."""
    with pytest.raises(ValidationError):
        InteractionRules.model_validate(
            {
                "method": "unknown",
                "minimum": minimum_rule(),
                "overtime": overtime_rule(),
            },
        )


def test_threshold_and_interaction_source_validation() -> None:
    """Only worked hours above threshold earn a premium; evidence is checked."""
    start = datetime(2026, 6, 2, 9, tzinfo=UTC)
    activity = Activity(
        activity_id="shift",
        resource_id="worker",
        starts_at=start,
        ends_at=start + timedelta(hours=2),
        resources=Decimal(1),
    )
    rules = InteractionRules(
        method="worked_overtime_ordinary_minimum_v1",
        minimum=minimum_rule(),
        overtime=overtime_rule(),
        rule_id="interaction",
        source_id="synthetic-award-1",
        source_sha256="a" * 64,
        citation="synthetic interaction clause",
        effective_from=date(2026, 1, 1),
        effective_to=date(2027, 1, 1),
        reviewed=True,
    )
    result = cost_minimum_with_overtime(release(), period(), rules, activity, "UTC")
    assert_that(result.total == Decimal(175))
    assert_that(result.interaction_citation == "synthetic interaction clause")
    with pytest.raises(ValueError, match="hash"):
        cost_minimum_with_overtime(
            release(),
            period(),
            rules.model_copy(update={"source_sha256": "b" * 64}),
            activity,
            "UTC",
        )
    with pytest.raises(ValueError, match="review"):
        cost_minimum_with_overtime(
            release(),
            period(),
            rules.model_copy(update={"reviewed": False}),
            activity,
            "UTC",
        )
