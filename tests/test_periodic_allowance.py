# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Test explicit periodic allowance calculation without inferring eligibility."""

from datetime import date
from decimal import Decimal
from fractions import Fraction

import pytest

from src.condition_history import release_sha256
from src.conditions import ConditionRelease
from src.periodic_allowance import (
    AllowancePeriod,
    AllowancePortion,
    cost_periodic_allowance,
)
from src.source_registry import SourceRegistry
from tests.checks import assert_that
from tests.test_conditions import condition
from tests.test_source_registry import source


def release() -> ConditionRelease:
    """Use a synthetic accepted annual amount and independently scoped source."""
    return ConditionRelease(
        release_id="synthetic",
        jurisdiction="QLD",
        employer="Synthetic employer",
        classification="Synthetic grade",
        sources=SourceRegistry(records=(source(),)),
        conditions=(condition("training", "fixed_annual", "1975", "AUD/year"),),
    )


def portion(label: str, hours: str, accrual: str, payment: str) -> AllowancePortion:
    """Create an explicitly reviewed test allocation."""
    return AllowancePortion(
        label=label,
        hours=Decimal(hours),
        accrual_factor=Decimal(accrual),
        payment_factor=Decimal(payment),
    )


def period(*portions: AllowancePortion) -> AllowancePeriod:
    """Use a caller-supplied 76-hour period and 26 periods per year."""
    return AllowancePeriod(
        starts_on=date(2026, 6, 1),
        ends_on=date(2026, 6, 15),
        full_time_hours=Decimal(76),
        periods_per_year=Decimal(26),
        portions=portions,
    )


def test_part_time_and_distinct_half_pay_accrual() -> None:
    """Prorate exact dollars and keep accrual separate from cash payment."""
    ordinary = portion("ordinary", "30.4", "1", "1")
    result = cost_periodic_allowance(release(), "training", period(ordinary))
    assert_that(result.payable == result.accrued == Fraction(395, 13))
    assert_that(result.condition.condition_id == "training")
    leave = portion("half-pay", "30.4", "1", "0.5")
    separate = cost_periodic_allowance(release(), "training", period(leave))
    assert_that(separate.accrued == Fraction(395, 13))
    assert_that(separate.payable == Fraction(395, 26))


def test_unpaid_and_overtime_depend_on_explicit_inputs() -> None:
    """Zero factors contribute nothing; no leave or overtime rules are inferred."""
    result = cost_periodic_allowance(
        release(),
        "training",
        period(portion("unpaid", "20", "0", "0")),
    )
    assert_that(result.accrued == result.payable == 0)


def test_invalid_or_changing_period_is_rejected() -> None:
    """Reject unsupported period scope and malformed copied allocations."""
    valid = period(portion("ordinary", "30", "1", "1"))
    crossed = valid.model_copy(update={"ends_on": date(2027, 1, 2)})
    with pytest.raises(ValueError, match="whole period"):
        cost_periodic_allowance(release(), "training", crossed)
    with pytest.raises(ValueError, match="whole period"):
        cost_periodic_allowance(release(), "missing", valid)
    excessive = valid.model_copy(update={"full_time_hours": Decimal(10)})
    with pytest.raises(ValueError, match="exceed"):
        cost_periodic_allowance(release(), "training", excessive)
    with pytest.raises(ValueError, match="unique"):
        period(portion("same", "1", "1", "1"), portion("same", "1", "1", "1"))


def test_split_period_retains_nominal_denominator_and_condition_lineage() -> None:
    """A mid-period rate change is split without charging a full period twice."""
    first = condition("first", "fixed_annual", "1975", "AUD/year").model_copy(
        update={"component": "training", "effective_to": date(2026, 6, 8)},
    )
    second = condition("second", "fixed_annual", "3950", "AUD/year").model_copy(
        update={"component": "training", "effective_from": date(2026, 6, 8)},
    )
    dated = release().model_copy(update={"conditions": (first, second)})
    first_half = period(portion("first-half", "38", "1", "1")).model_copy(
        update={"ends_on": date(2026, 6, 8)},
    )
    second_half = period(portion("second-half", "38", "1", "1")).model_copy(
        update={"starts_on": date(2026, 6, 8)},
    )
    before = cost_periodic_allowance(dated, "training", first_half)
    after = cost_periodic_allowance(dated, "training", second_half)
    assert_that(before.payable + after.payable == Fraction(5925, 52))
    assert_that(before.condition.condition_id == "first")
    assert_that(after.condition.condition_id == "second")
    assert_that(before.release_sha256 == after.release_sha256)
    assert_that(before.release_sha256 == release_sha256(dated))
