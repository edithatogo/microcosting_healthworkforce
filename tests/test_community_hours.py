# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Check both sides of each community-hours schedule breakpoint."""

import pytest

from src.community_hours import tas_rural_base_community_hours
from tests.checks import assert_that


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
