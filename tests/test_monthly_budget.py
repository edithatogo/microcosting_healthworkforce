# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Calendar-month salary budgeting is an explicit scenario, not payroll."""

from datetime import date
from decimal import Decimal
from fractions import Fraction

import pytest

from src.monthly_budget import MonthlySalaryRate, monthly_salary_budget
from tests.checks import assert_that


def rate(identity: str, start: date, end: date, salary: str) -> MonthlySalaryRate:
    """Build a synthetic monthly-aligned salary rate."""
    return MonthlySalaryRate(
        rate_id=identity,
        effective_from=start,
        effective_to=end,
        annual_salary=Decimal(salary),
    )


def test_partial_leap_month_and_rate_change() -> None:
    """Apply inclusive days and the correct effective salary in each month."""
    rates = (
        rate("old", date(2024, 2, 1), date(2024, 3, 1), "120000"),
        rate("new", date(2024, 3, 1), date(2024, 4, 1), "144000"),
    )
    result = monthly_salary_budget(
        date(2024, 2, 15),
        date(2024, 3, 10),
        Decimal("0.5"),
        rates,
    )
    assert_that([r.covered_days for r in result.rows] == [15, 10])
    assert_that(result.total == Fraction(5000 * 15, 29) + Fraction(6000 * 10, 31))
    assert_that([r.rate.rate_id for r in result.rows] == ["old", "new"])


def test_full_year_and_one_day() -> None:
    """Reproduce the annual amount and a single leap-day share."""
    rates = (rate("r", date(2024, 1, 1), date(2025, 1, 1), "120000"),)
    annual = monthly_salary_budget(
        date(2024, 1, 1),
        date(2024, 12, 31),
        Decimal(1),
        rates,
    )
    daily = monthly_salary_budget(
        date(2024, 2, 29),
        date(2024, 2, 29),
        Decimal(1),
        rates,
    )
    assert_that(annual.total == Fraction(120000))
    assert_that(daily.total == Fraction(10000, 29))


def test_rejects_gaps_overlaps_invalid_inputs_and_partial_rate_month() -> None:
    """Reject ambiguous or invalid scenario inputs."""
    first = rate("a", date(2024, 1, 1), date(2024, 2, 1), "120000")
    with pytest.raises(ValueError, match="missing"):
        monthly_salary_budget(date(2024, 1, 1), date(2024, 2, 1), Decimal(1), (first,))
    with pytest.raises(ValueError, match="overlap"):
        monthly_salary_budget(
            date(2024, 1, 1),
            date(2024, 1, 2),
            Decimal(1),
            (first, rate("b", date(2024, 1, 1), date(2024, 3, 1), "1")),
        )
    with pytest.raises(ValueError, match="whole calendar"):
        rate("c", date(2024, 1, 2), date(2024, 2, 1), "1")
    with pytest.raises(ValueError, match="FTE"):
        monthly_salary_budget(
            date(2024, 1, 1),
            date(2024, 1, 2),
            Decimal("NaN"),
            (first,),
        )
    with pytest.raises(ValueError, match="Duplicate"):
        monthly_salary_budget(
            date(2024, 1, 1),
            date(2024, 1, 2),
            Decimal(1),
            (first, first),
        )
