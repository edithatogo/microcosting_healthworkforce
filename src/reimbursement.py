# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Cost approved expense claims against one explicitly reviewed cap period."""

from dataclasses import dataclass
from fractions import Fraction
from typing import Self
lazy from datetime import date
lazy from decimal import Decimal

from pydantic import Field, model_validator

from src.unit_quotes import QuoteModel


class ReimbursementClaim(QuoteModel):
    """An approved eligible amount and its assigned cap accounting date."""

    claim_id: str
    charged_on: date
    eligible_amount: Decimal = Field(ge=0, allow_inf_nan=False)
    approval_evidence: str


class ReimbursementPeriod(QuoteModel):
    """A reviewed cap in one currency for one assignment and accounting period."""

    currency: str = Field(pattern=r"^[A-Z]{3}$")
    starts_on: date
    ends_on: date
    cap: Decimal = Field(ge=0, allow_inf_nan=False)
    prior_use: Decimal = Field(ge=0, allow_inf_nan=False)
    applicability_evidence: str
    claims: tuple[ReimbursementClaim, ...]

    @model_validator(mode="after")
    def validate_period(self) -> Self:
        """Require a usable cap and unique claims in declared accounting order."""
        dates = [claim.charged_on for claim in self.claims]
        if (
            self.starts_on >= self.ends_on
            or self.prior_use > self.cap
            or any(not self.starts_on <= day < self.ends_on for day in dates)
            or dates != sorted(dates)
            or len({claim.claim_id for claim in self.claims}) != len(self.claims)
        ):
            msg = "Invalid reimbursement period, cap consumption or claim order"
            raise ValueError(msg)
        return self


@dataclass(frozen=True)
class ReimbursementRow:
    """Cost and remaining cap after one approved claim."""

    claim: ReimbursementClaim
    cost: Fraction
    remaining: Fraction


def cost_reimbursements(
    period: ReimbursementPeriod,
) -> tuple[ReimbursementRow, ...]:
    """Apply the supplied cap to approved expenses in the declared order.

    The caller determines coverage, proration, eligible costs and the period
    to charge. A cap alone creates no cost.
    """
    period = ReimbursementPeriod.model_validate(period.model_dump())
    remaining = Fraction(period.cap) - Fraction(period.prior_use)
    rows: list[ReimbursementRow] = []
    for claim in period.claims:
        cost = min(Fraction(claim.eligible_amount), remaining)
        remaining -= cost
        rows.append(ReimbursementRow(claim, cost, remaining))
    return tuple(rows)
