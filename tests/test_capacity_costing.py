# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Explicit productive-capacity and incremental cover scenario arithmetic."""

from datetime import date
from decimal import Decimal
from fractions import Fraction

import pytest

from src.capacity_costing import CapacityLoss, CapacityScenarioInputs, capacity_scenario
from tests.checks import assert_that
from tests.test_roster_costing import release


def test_incremental_cover_is_added_once_to_paid_cost() -> None:
    """Paid salary remains intact and 100 cover hours at $60 add $6000."""
    scenario = capacity_scenario(
        release(),
        date(2026, 6, 1),
        CapacityScenarioInputs(
            losses=(CapacityLoss(loss_id="leave", hours=Decimal(200)),),
            cover_hours=Decimal(100),
            cover_hourly_cost=Decimal(60),
            losses_disjoint=True,
        ),
    )
    assert_that(scenario.paid_cost == Decimal(100000))
    assert_that(scenario.productive_hours == Decimal(1800))
    assert_that(scenario.incremental_cover_cost == Decimal(6000))
    assert_that(scenario.total_cost == Decimal(106000))


def test_capacity_rejects_excess_loss_and_double_counted_id() -> None:
    """No negative productive capacity or repeated category is inferred."""
    loss = CapacityLoss(loss_id="leave", hours=Decimal(1200))
    with pytest.raises(ValueError, match="Duplicate"):
        capacity_scenario(
            release(),
            date(2026, 6, 1),
            CapacityScenarioInputs(
                losses=(loss, loss),
                cover_hours=Decimal(0),
                cover_hourly_cost=Decimal(0),
                losses_disjoint=True,
            ),
        )
    with pytest.raises(ValueError, match="productive"):
        capacity_scenario(
            release(),
            date(2026, 6, 1),
            CapacityScenarioInputs(
                losses=(CapacityLoss(loss_id="excess", hours=Decimal(2000)),),
                cover_hours=Decimal(0),
                cover_hourly_cost=Decimal(0),
                losses_disjoint=True,
            ),
        )


def test_capacity_ratio_retains_exact_nonterminating_value() -> None:
    """Scenario productive-hour ratios retain exact values before rounding."""
    inputs = CapacityScenarioInputs(
        losses=(CapacityLoss(loss_id="leave", hours=Decimal(200)),),
        cover_hours=Decimal(100),
        cover_hourly_cost=Decimal(60),
        losses_disjoint=True,
    )
    result = capacity_scenario(release(), date(2026, 6, 1), inputs)
    assert_that(
        Fraction(result.exact_total_numerator, result.exact_total_denominator)
        == Fraction(106000),
    )
    assert_that(
        Fraction(
            result.exact_productive_rate_numerator,
            result.exact_productive_rate_denominator,
        )
        == Fraction(530, 9),
    )


def test_paid_cost_avoids_intermediate_hourly_rounding() -> None:
    """Converting a nonterminating hourly rate must preserve annual salary."""
    baseline = release()
    revised = baseline.model_copy(
        update={
            "conditions": tuple(
                item.model_copy(
                    update={
                        "value": Decimal(300002 if item.kind == "salary" else 2001),
                    },
                )
                for item in baseline.conditions
            ),
        },
    )
    result = capacity_scenario(
        revised,
        date(2026, 6, 1),
        CapacityScenarioInputs(
            losses=(),
            cover_hours=Decimal(0),
            cover_hourly_cost=Decimal(0),
            losses_disjoint=True,
        ),
    )
    assert_that(result.paid_cost == result.total_cost == Decimal(300002))
