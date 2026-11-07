# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Check both sides of each community-hours schedule breakpoint."""

from fractions import Fraction

import pytest

from src.community_hours import (
    price_tas_rural_community_hours,
    tas_rural_base_community_hours,
    tas_rural_community_hours,
)
from tests.checks import assert_that
from tests.test_unit_quotes import quantity, quote, release


@pytest.mark.parametrize(
    ("population", "hours"),
    [(4999, 2), (5001, 3), (9999, 3), (10001, 4)],
)
def test_community_hours_schedule(population: int, hours: int) -> None:
    """Return the community quantity in each covered band."""
    assert_that(tas_rural_base_community_hours(population) == hours)


@pytest.mark.parametrize("population", [5000, 10000])
def test_exact_breakpoints_are_uncovered(population: int) -> None:
    """Preserve the source's strict inequalities."""
    with pytest.raises(ValueError, match="uncovered schedule breakpoint"):
        tas_rural_base_community_hours(population)


def test_volunteer_ambulance_increment_applies_once_to_covered_pool() -> None:
    """Apply the extra hours once and preserve uncovered base thresholds."""
    supported_hours, unsupported_hours = 5, 3
    assert_that(
        tas_rural_community_hours(5001, supports_volunteer_ambulance=True)
        == supported_hours,
    )
    assert_that(
        tas_rural_community_hours(5001, supports_volunteer_ambulance=False)
        == unsupported_hours,
    )
    with pytest.raises(ValueError, match="uncovered schedule breakpoint"):
        tas_rural_community_hours(5000, supports_volunteer_ambulance=True)


def test_community_hours_price_negotiated_shares() -> None:
    """Convert each exact share to hours before hourly pricing."""
    rates = release(quote(unit="hour"))
    first = quantity(unit="hour", quantity=Fraction(1, 3))
    second = quantity(unit="hour", quantity=Fraction(2, 3), quantity_id="second")
    result = price_tas_rural_community_hours(
        rates,
        5001,
        (first, second),
        supports_volunteer_ambulance=True,
    )
    assert_that(
        [row.quantity.quantity for row in result.rows]
        == [
            Fraction(5, 3),
            Fraction(10, 3),
        ],
    )
    assert_that(result.total == Fraction("500.05"))
    with pytest.raises(ValueError, match="full shares"):
        price_tas_rural_community_hours(
            rates,
            5001,
            (first,),
            supports_volunteer_ambulance=True,
        )
