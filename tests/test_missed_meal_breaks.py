# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Check the Ambulance Tasmania missed-break quantity against dated pricing."""

from decimal import Decimal
from fractions import Fraction

import pytest

from src.missed_meal_breaks import missed_break_overtime_quantity
from src.unit_quotes import price_units
from tests.checks import assert_that
from tests.test_unit_quotes import quantity, quote, release


@pytest.mark.parametrize("missed", [0, 1, 2])
def test_missed_breaks_price_paid_exposure(missed: int) -> None:
    """Price reviewed missed breaks at an explicit synthetic overtime rate."""
    breaks = quantity(unit="break", quantity=Decimal(missed))
    overtime = missed_break_overtime_quantity(breaks)
    rates = release(quote(unit="hour", amount=Decimal(80)))
    assert_that(overtime.quantity == Fraction(missed, 2))
    assert_that(price_units(rates, (overtime,)).total == Fraction(40 * missed))


@pytest.mark.parametrize(
    ("unit", "count"),
    [("hour", "1"), ("break", "1.5"), ("break", "3")],
)
def test_invalid_missed_break_quantity(unit: str, count: str) -> None:
    """Require a whole count within the reviewed two-break scope."""
    with pytest.raises(ValueError, match="reviewed missed breaks"):
        missed_break_overtime_quantity(quantity(unit=unit, quantity=Decimal(count)))


def test_separate_meal_occurrences_and_overtime() -> None:
    """Retain all reviewed spoiled-meal occasions beside distinct payments."""
    rates = release(
        quote(unit="hour", component="missed-break", amount=Decimal(80)),
        quote(
            quote_id="spoiled",
            component="spoiled-meal",
            unit="occasion",
            amount=Decimal("29.20"),
        ),
        quote(
            quote_id="training",
            component="away-training-meal",
            unit="occasion",
            amount=Decimal("29.20"),
        ),
    )
    spoiled = tuple(
        quantity(quantity_id=f"spoiled-{index}", quote_id="spoiled", unit="occasion")
        for index in range(3)
    )
    training = quantity(quantity_id="training", quote_id="training", unit="occasion")
    overtime = missed_break_overtime_quantity(quantity(unit="break"))
    result = price_units(rates, (*spoiled, training, overtime))
    assert_that(result.total == Fraction("156.80"))
