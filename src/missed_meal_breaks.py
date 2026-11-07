# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Convert reviewed missed meal breaks to paid overtime exposure."""

from fractions import Fraction

from src.unit_quotes import QuoteQuantity


def missed_break_overtime_quantity(breaks: QuoteQuantity) -> QuoteQuantity:
    """Return half an hour of paid exposure per reviewed missed break.

    The caller supplies the shift-end valuation date and an applicable hourly
    overtime quote. Interrupted breaks and worked hours are tracked separately.
    """
    breaks = QuoteQuantity.model_validate(dict(breaks))
    if breaks.unit != "break" or breaks.quantity not in (0, 1, 2):
        msg = "Expected zero, one or two reviewed missed breaks"
        raise ValueError(msg)
    return QuoteQuantity.model_validate(
        dict(breaks, unit="hour", quantity=Fraction(breaks.quantity) / 2),
    )
