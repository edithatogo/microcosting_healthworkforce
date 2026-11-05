# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Check inverse conversion of annual amounts and hourly rates."""

import math

import polars as pl
from hypothesis import given
from hypothesis import strategies as st

from src.polars_rates import annual_to_rates
from tests.checks import assert_that


@given(st.integers(0, 1000000), st.integers(1, 80))
def test_hourly_rate_recovers_annual_amount(salary: int, hours: int) -> None:
    """Annual and hourly valuations agree at the contracted hours."""
    frame = pl.DataFrame(
        {"Grade(s)_Hours per week": [hours], "Calculated_Cost_LL_Y0": [salary]},
    )
    rate = annual_to_rates(frame).item(0, "Calculated_Hourly_LL_Y0")
    assert_that(math.isclose(rate * 52 * hours, salary))
