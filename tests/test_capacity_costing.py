# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Explicit productive-capacity and incremental cover scenario arithmetic."""

from datetime import date
from decimal import Decimal
from fractions import Fraction

import pytest

from src.capacity_costing import CapacityLoss, CapacityScenarioInputs, capacity_scenario
from src.leave_pricing import sa_part_time_study_paid_hours
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


def test_paid_development_leave_reduces_capacity_without_adding_wages() -> None:
    """Five reviewed days reduce the service denominator within paid hours."""
    result = capacity_scenario(
        release(),
        date(2026, 6, 1),
        CapacityScenarioInputs(
            losses=(
                CapacityLoss(loss_id="annual-leave", hours=Decimal(152)),
                CapacityLoss(loss_id="paid-development-leave", hours=Decimal(38)),
            ),
            cover_hours=Decimal(0),
            cover_hourly_cost=Decimal(0),
            losses_disjoint=True,
        ),
    )
    assert_that(result.productive_hours == Decimal(1810))
    assert_that(result.paid_cost == result.total_cost == Decimal(100000))
    assert_that(
        Fraction(
            result.exact_productive_rate_numerator,
            result.exact_productive_rate_denominator,
        )
        == Fraction(10000, 181),
    )


def test_approved_sa_study_hours_preserve_exact_capacity_ratio() -> None:
    """Reviewed study and travel affect service hours without adding salary."""
    study = sa_part_time_study_paid_hours(Fraction(5), Fraction(1, 3))
    inputs = CapacityScenarioInputs(
        losses=(CapacityLoss(loss_id="approved-study", hours=study),),
        cover_hours=Decimal(0),
        cover_hourly_cost=Decimal(0),
        losses_disjoint=True,
    )
    result = capacity_scenario(
        release(),
        date(2026, 6, 1),
        CapacityScenarioInputs.model_validate_json(inputs.model_dump_json()),
    )
    assert_that(result.total_cost == Decimal(100000))
    assert_that(
        Fraction(
            result.exact_productive_rate_numerator,
            result.exact_productive_rate_denominator,
        )
        == Fraction(300000, 5984),
    )


def test_partial_leave_backfill_prices_replacement_hours_separately() -> None:
    """Cover half of four 38-hour leave weeks without reducing paid cost."""
    scenario = capacity_scenario(
        release(),
        date(2026, 6, 1),
        CapacityScenarioInputs(
            losses=(CapacityLoss(loss_id="annual-leave", hours=Decimal(152)),),
            cover_hours=Decimal(76),
            cover_hourly_cost=Decimal(50),
            losses_disjoint=True,
        ),
    )
    assert_that(scenario.productive_hours == Decimal(1848))
    assert_that(scenario.assumptions.cover_hours == Decimal(76))
    assert_that(scenario.incremental_cover_cost == Decimal(3800))
    assert_that(scenario.total_cost == Decimal(103800))


def test_fractional_cover_hours_preserve_exact_cost() -> None:
    """A third of an hour at 50 retains its exact cost in the ledger total."""
    result = capacity_scenario(
        release(),
        date(2026, 6, 1),
        CapacityScenarioInputs(
            losses=(CapacityLoss(loss_id="leave", hours=Decimal(1)),),
            cover_hours=Fraction(1, 3),
            cover_hourly_cost=Decimal(50),
            losses_disjoint=True,
        ),
    )
    assert_that(result.assumptions.cover_hours == Fraction(1, 3))
    exact = Fraction(result.exact_total_numerator, result.exact_total_denominator)
    assert_that(exact == Fraction(100000) + Fraction(50, 3))
