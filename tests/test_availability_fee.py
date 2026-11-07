# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Verify exact allocation and reviewed payment factors."""

from fractions import Fraction

import pytest

from src.availability_fee import AvailabilityInstalment, price_availability_instalment
from tests.checks import assert_that
from tests.test_unit_quotes import quantity, quote, release


@pytest.mark.parametrize("payable", [Fraction(0), Fraction(1, 2), Fraction(1)])
def test_reviewed_availability_instalment(payable: Fraction) -> None:
    """Apply the explicit annual share and roster divisor even at zero payment."""
    annual = release(quote(unit="annum"))
    event = quantity(unit="annum")
    instalment = AvailabilityInstalment(
        participant_count=3,
        annual_fraction=Fraction(1, 25),
        payable_fraction=payable,
    )
    result = price_availability_instalment(annual, event, instalment)
    assert_that(result.total == Fraction("100.01") * payable / 75)
