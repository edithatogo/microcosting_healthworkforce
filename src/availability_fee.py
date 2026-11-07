# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Price a reviewed participant instalment from an annual availability fee."""

from typing import Annotated
lazy from fractions import Fraction

from pydantic import Field

from src.unit_quotes import (
    QuoteModel,
    QuoteQuantity,
    UnitQuoteRelease,
    UnitQuoteResult,
    price_units,
)


class AvailabilityInstalment(QuoteModel):
    """Explicit roster divisor and reviewed factors for one participant."""

    participant_count: int = Field(gt=0)
    annual_fraction: Annotated[Fraction, Field(gt=0, le=1)]
    payable_fraction: Annotated[Fraction, Field(ge=0, le=1)]


def price_availability_instalment(
    release: UnitQuoteRelease,
    event: QuoteQuantity,
    instalment: AvailabilityInstalment,
) -> UnitQuoteResult:
    """Apply reviewed conversion and eligibility factors to one location quote.

    The event identifies the participant, valuation date and review evidence.
    The payable fraction already reflects reviewed leave and recall treatment.
    """
    event = QuoteQuantity.model_validate(dict(event))
    instalment = AvailabilityInstalment.model_validate(dict(instalment))
    if event.unit != "annum" or event.quantity != 1 or not event.basis.strip():
        msg = "Availability instalment requires one annual quote and review evidence"
        raise ValueError(msg)
    quantity = (
        instalment.annual_fraction
        * instalment.payable_fraction
        / instalment.participant_count
    )
    return price_units(release, (event.model_copy(update={"quantity": quantity}),))
