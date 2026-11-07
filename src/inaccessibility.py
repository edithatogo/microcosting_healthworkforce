# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Inaccessibility payments for a reviewed single-category appointment."""

from fractions import Fraction
from typing import Annotated, Literal
lazy from datetime import date
lazy from decimal import Decimal

from pydantic import Field

from src.unit_quotes import (
    QuoteModel,
    QuoteQuantity,
    UnitQuoteRelease,
    UnitQuoteResult,
    price_units,
)


class InaccessibilityPaymentBasis(QuoteModel):
    """Reviewed category, quote and employment share for a single payment."""

    category: Literal[1, 2, 3, 4, 5, 6, 7]
    payment_id: str
    annual_quote_id: str
    valued_on: date
    service_assessed_through: date
    employment_fraction: Decimal = Field(gt=0, le=1, allow_inf_nan=False)
    review_evidence: str


class InaccessibilityFirstPayment(InaccessibilityPaymentBasis):
    """Reviewed inputs for the standard first-payment service milestone."""

    completed_eligible_months: int = Field(ge=0)
    first_payment_already_paid: bool


class InaccessibilityRecurringPayment(InaccessibilityPaymentBasis):
    """Reviewed service and payment history for one three-month instalment."""

    initial_milestone_met: bool
    instalment_service_complete: bool
    instalment_already_paid: bool


def price_inaccessibility_first_payment(
    release: UnitQuoteRelease,
    request: InaccessibilityFirstPayment,
) -> UnitQuoteResult:
    """Calculate the outstanding first payment for the supplied standard history."""
    request = InaccessibilityFirstPayment.model_validate(request.model_dump())
    threshold = 6 if request.category in (1, 2, 3) else 12
    eligible = (
        not request.first_payment_already_paid
        and request.completed_eligible_months >= threshold
    )
    return _price_payment(
        release,
        request,
        Fraction(threshold, 12) if eligible else Fraction(0),
    )


def price_inaccessibility_recurring_payment(
    release: UnitQuoteRelease,
    request: InaccessibilityRecurringPayment,
) -> UnitQuoteResult:
    """Price a reviewed unpaid instalment after the initial service milestone."""
    request = InaccessibilityRecurringPayment.model_validate(request.model_dump())
    eligible = (
        request.initial_milestone_met
        and request.instalment_service_complete
        and not request.instalment_already_paid
    )
    return _price_payment(
        release,
        request,
        Fraction(1, 4) if eligible else Fraction(0),
    )


def _price_payment(
    release: UnitQuoteRelease,
    request: InaccessibilityPaymentBasis,
    annual_fraction: Fraction,
) -> UnitQuoteResult:
    if request.service_assessed_through > request.valued_on:
        msg = "Service assessment cannot follow payment valuation"
        raise ValueError(msg)
    quantity = QuoteQuantity(
        quantity_id=request.payment_id,
        quote_id=request.annual_quote_id,
        unit="annum",
        valued_on=request.valued_on,
        quantity=Fraction(request.employment_fraction) * annual_fraction,
        quantity_kind="analyst_assumption",
        basis=request.review_evidence,
    )
    result = price_units(release, (quantity,))
    if result.rows[0].quote.component != f"inaccessibility-category-{request.category}":
        msg = "Annual quote must match the inaccessibility category"
        raise ValueError(msg)
    return result


class InaccessibilityRotationPayment(InaccessibilityPaymentBasis):
    """Reviewed single-category vocational rotations within one calendar year."""

    service_year: int = Field(ge=1, le=9999)
    completed_eligible_months: int = Field(ge=0, le=12)
    recognised_vocational_rmo: bool
    reviewed_annual_fraction: (
        Annotated[Decimal, Field(ge=0, le=1, allow_inf_nan=False)]
        | Annotated[Fraction, Field(ge=0, le=1)]
    )
    payment_already_paid: bool


def price_inaccessibility_rotation_payment(
    release: UnitQuoteRelease,
    request: InaccessibilityRotationPayment,
) -> UnitQuoteResult:
    """Apply the four-month threshold to reviewed vocational rotation service."""
    request = InaccessibilityRotationPayment.model_validate(dict(request))
    minimum_months = 4
    if (
        request.service_assessed_through.year != request.service_year
        or request.valued_on < request.service_assessed_through
    ):
        msg = "Rotation service assessment must be in its service year and by valuation"
        raise ValueError(msg)
    eligible = (
        request.recognised_vocational_rmo
        and request.completed_eligible_months >= minimum_months
        and not request.payment_already_paid
    )
    return _price_payment(
        release,
        request,
        Fraction(request.reviewed_annual_fraction) if eligible else Fraction(0),
    )
