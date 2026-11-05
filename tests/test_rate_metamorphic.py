# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Algebraic properties of rate conversion, independent of scientific priors."""

import math

import polars as pl
import pytest
from hypothesis import given
from hypothesis import strategies as st
from polars.testing import assert_frame_equal

from src.polars_rates import annual_to_rates, productive_hourly_rates
from tests.checks import assert_that


@given(st.integers(1, 1000000), st.integers(1, 80), st.integers(1, 20))
def test_currency_scaling(salary: int, hours: int, factor: int) -> None:
    """Changing currency scale changes all derived rates by the same factor."""
    frame = pl.DataFrame(
        {"Grade(s)_Hours per week": [hours], "Calculated_Cost_LL_Y0": [salary]},
    )
    base = annual_to_rates(frame)
    scaled = annual_to_rates(
        frame.with_columns(pl.col("Calculated_Cost_LL_Y0") * factor),
    )
    for unit in ("Hourly", "Daily", "Weekly", "Fortnightly", "Monthly"):
        column = f"Calculated_{unit}_LL_Y0"
        assert_that(math.isclose(scaled.item(0, column), base.item(0, column) * factor))


@given(st.integers(1, 1000000), st.integers(1, 80))
def test_partition_and_permutation(salary: int, hours: int) -> None:
    """Rates preserve row identity and are independent of batching and order."""
    frame = pl.DataFrame(
        {
            "id": [0, 1],
            "Grade(s)_Hours per week": [hours, hours + 1],
            "Calculated_Cost_LL_Y0": [salary, salary + 100],
        },
    )
    expected = annual_to_rates(frame)
    assert_frame_equal(annual_to_rates(frame.reverse()).reverse(), expected)
    partitioned = pl.concat(
        [annual_to_rates(frame.head(1)), annual_to_rates(frame.tail(1))],
    )
    assert_frame_equal(partitioned, expected, check_exact=False, rel_tol=1e-12)


@given(st.integers(1, 1000000), st.floats(0.1, 0.5, allow_nan=False))
def test_productive_time_inverse(salary: int, productive: float) -> None:
    """Doubling available productive hours halves both hourly valuations."""
    frame = pl.DataFrame(
        {
            "salary": [salary],
            "loading": [0.175],
            "on_cost_fraction": [0.1],
            "development": [500.0],
            "productive": [productive],
            "hours": [38.0],
            "weeks": [4.0],
        },
    )
    base = productive_hourly_rates(frame)
    doubled = productive_hourly_rates(
        frame.with_columns(pl.col("productive") * 2),
    )
    for column in ("original_hourly", "leave_cover_only_hourly"):
        assert_that(math.isclose(doubled.item(0, column) * 2, base.item(0, column)))


def test_rate_units_and_missing_hours() -> None:
    """A 52-week annual amount has independently specified periodic values."""
    fallback = 9.0
    frame = pl.DataFrame(
        {
            "Grade(s)_Hours per week": [38.0, 0.0, -1.0],
            "Calculated_Cost_LL_Y0": [1976.0, 1976.0, 1976.0],
            "Calculated_Cost_Mid_Y1": [3952.0, 3952.0, 3952.0],
            "Base Salary + Costs (hourly)_LL": [9.0, 9.0, 9.0],
        },
    )
    result = annual_to_rates(frame)
    for unit, value in {
        "Hourly": 1.0,
        "Daily": 7.6,
        "Weekly": 38.0,
        "Fortnightly": 76.0,
        "Monthly": 1976.0 / 12,
    }.items():
        assert_that(math.isclose(result.item(0, f"Calculated_{unit}_LL_Y0"), value))
        assert_that(
            math.isclose(result.item(0, f"Calculated_{unit}_Mid_Y1"), value * 2),
        )
    assert_that(result.item(1, "Calculated_Hourly_LL_Y0") == fallback)
    assert_that(result.item(2, "Calculated_Hourly_LL_Y0") == fallback)
    assert_that(result.item(1, "Calculated_Hourly_Mid_Y1") is None)
    assert_that(result.item(1, "Calculated_Daily_LL_Y0") is None)


def test_leave_cover_values_and_domain() -> None:
    """Independently value a synthetic year and reject invalid denominators."""
    frame = pl.DataFrame(
        {
            "salary": [52000.0],
            "loading": [0.25],
            "on_cost_fraction": [0.1],
            "development": [520.0],
            "productive": [1.0],
            "hours": [38.0],
            "weeks": [4.0],
        },
    )
    result = productive_hourly_rates(frame)
    assert_that(math.isclose(result.item(0, "original_hourly"), 127720 / 1976))
    assert_that(math.isclose(result.item(0, "leave_cover_only_hourly"), 62720 / 1976))
    for column, value in (
        ("productive", 0.0),
        ("productive", -0.1),
        ("productive", 1.01),
        ("hours", 0.0),
        ("hours", -1.0),
        ("salary", None),
    ):
        with pytest.raises(ValueError, match="positive productive hours"):
            productive_hourly_rates(frame.with_columns(pl.lit(value).alias(column)))
