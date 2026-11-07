# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Cost approved expense claims against one explicitly reviewed cap period."""

from dataclasses import dataclass
from fractions import Fraction
from typing import Literal, Self
lazy from datetime import date
lazy from decimal import Decimal

from pydantic import Field, model_validator

from src.unit_quotes import NonnegativeQuantity, QuoteModel


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
    cap: NonnegativeQuantity
    prior_use: NonnegativeQuantity
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
    period = ReimbursementPeriod.model_validate(
        {**dict(period), "claims": tuple(dict(claim) for claim in period.claims)},
    )
    remaining = Fraction(period.cap) - Fraction(period.prior_use)
    rows: list[ReimbursementRow] = []
    for claim in period.claims:
        cost = min(Fraction(claim.eligible_amount), remaining)
        remaining -= cost
        rows.append(ReimbursementRow(claim, cost, remaining))
    return tuple(rows)


class ReimbursementCarryDecision(QuoteModel):
    """Reviewed closing balances and the ceiling available for carry-over."""

    current_remaining: NonnegativeQuantity
    prior_remaining: NonnegativeQuantity
    carry_limit: NonnegativeQuantity
    eligible_balances: Literal["none", "current", "current_and_prior"]
    decision_evidence: str


def reimbursement_carry_amount(decision: ReimbursementCarryDecision) -> Fraction:
    """Value eligible carry using an explicit limit and reviewed balance split.

    The limit is the amount available for carry after any other allocations
    under the applicable accumulation ceiling. No claim allocation, employer
    transfer or cash payment is implied.
    """
    decision = ReimbursementCarryDecision.model_validate(dict(decision))
    if decision.eligible_balances == "none":
        return Fraction(0)
    eligible = Fraction(decision.current_remaining)
    if decision.eligible_balances == "current_and_prior":
        eligible += Fraction(decision.prior_remaining)
    return min(eligible, Fraction(decision.carry_limit))
