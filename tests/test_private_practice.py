# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Test the exact qualifying-income threshold for a dated wage comparison."""

from datetime import date
from decimal import Decimal
from fractions import Fraction

import pytest

from src.private_practice import (
    PrivatePracticeComparison,
    compare_private_practice_wages,
)
from tests.checks import assert_that
from tests.test_unit_quotes import quote, release


def test_private_practice_wage_threshold_and_dates() -> None:
    """Equality qualifies while one cent less and expired prices fail."""
    quotes = release(
        quote(
            quote_id="ordinary",
            component="ordinary",
            unit="week",
            amount=Decimal(500),
        ),
        quote(
            quote_id="lower",
            component="private_practice_wage",
            unit="week",
            amount=Decimal("390.25"),
        ),
    )
    facts = PrivatePracticeComparison(
        ordinary_quote_id="ordinary",
        private_practice_quote_id="lower",
        valued_on=date(2026, 6, 1),
        qualifying_income=Decimal("109.75"),
        evidence="Synthetic reviewed income",
    )
    result = compare_private_practice_wages(quotes, facts)
    assert_that(result.required_income == Fraction("109.75"))
    assert_that(result.lower_wage_available)
    below = facts.model_copy(update={"qualifying_income": Decimal("109.74")})
    assert_that(not compare_private_practice_wages(quotes, below).lower_wage_available)
    expired = facts.model_copy(update={"valued_on": date(2027, 1, 1)})
    with pytest.raises(ValueError, match="outside"):
        compare_private_practice_wages(quotes, expired)


def test_private_practice_threshold_changes_at_new_quote_boundary() -> None:
    """The same income can qualify before a new weekly rate takes effect."""
    boundary = date(2026, 7, 1)
    before = quote(
        quote_id="before",
        component="ordinary",
        unit="week",
        amount=Decimal(500),
        ends_on=boundary,
    )
    after = quote(
        quote_id="after",
        component="ordinary",
        unit="week",
        amount=Decimal(520),
        starts_on=boundary,
    )
    lower = quote(
        quote_id="lower",
        component="private_practice_wage",
        unit="week",
        amount=Decimal(400),
    )
    quotes = release(before, after, lower)
    facts = PrivatePracticeComparison(
        ordinary_quote_id="before",
        private_practice_quote_id="lower",
        valued_on=date(2026, 6, 30),
        qualifying_income=Decimal(110),
        evidence="Synthetic reviewed income",
    )
    old = compare_private_practice_wages(quotes, facts)
    new = compare_private_practice_wages(
        quotes,
        facts.model_copy(update={"ordinary_quote_id": "after", "valued_on": boundary}),
    )
    assert_that(old.lower_wage_available and not new.lower_wage_available)
    assert_that(new.required_income == Fraction(120))
    assert_that(new.ordinary.cost == Fraction(520))
    assert_that(new.private_practice.cost == Fraction(400))
    assert_that(new.release_sha256 == old.release_sha256)
