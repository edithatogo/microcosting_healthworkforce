# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Compare source-priced weekly wages with reviewed private-practice income."""

from dataclasses import dataclass
from fractions import Fraction
lazy from datetime import date

from src.unit_quotes import (
    NonnegativeQuantity,
    QuoteModel,
    QuoteQuantity,
    UnitQuoteCost,
    UnitQuoteRelease,
    price_units,
)


class PrivatePracticeComparison(QuoteModel):
    """One week's scoped alternatives and its reviewed qualifying income."""

    ordinary_quote_id: str
    private_practice_quote_id: str
    valued_on: date
    qualifying_income: NonnegativeQuantity
    evidence: str


@dataclass(frozen=True)
class PrivatePracticeResult:
    """Keep alternative wages and qualifying income visible and separate."""

    comparison: PrivatePracticeComparison
    release_sha256: str
    currency: str
    ordinary: UnitQuoteCost
    private_practice: UnitQuoteCost
    required_income: Fraction
    lower_wage_available: bool


def compare_private_practice_wages(
    release: UnitQuoteRelease,
    comparison: PrivatePracticeComparison,
) -> PrivatePracticeResult:
    """Test the minimum-income condition without electing an employer wage."""
    comparison = PrivatePracticeComparison.model_validate(dict(comparison))
    alternatives = price_units(
        release,
        tuple(
            QuoteQuantity(
                quantity_id=label,
                quote_id=identity,
                unit="week",
                quantity=Fraction(1),
                valued_on=comparison.valued_on,
                quantity_kind="analyst_assumption",
                basis=comparison.evidence,
            )
            for label, identity in (
                ("ordinary", comparison.ordinary_quote_id),
                ("private-practice", comparison.private_practice_quote_id),
            )
        ),
    )
    ordinary, lower = alternatives.rows
    if lower.cost >= ordinary.cost:
        msg = "Private-practice wage must be below the ordinary alternative"
        raise ValueError(msg)
    required = ordinary.cost - lower.cost
    return PrivatePracticeResult(
        comparison,
        alternatives.release_sha256,
        alternatives.currency,
        ordinary,
        lower,
        required,
        Fraction(comparison.qualifying_income) >= required,
    )
