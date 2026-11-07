# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Cost approved expense claims within one explicitly reviewed accounting period."""

from dataclasses import dataclass
from fractions import Fraction
from typing import Literal, Self
lazy from datetime import date

from pydantic import Field, model_validator

from src.unit_quotes import NonnegativeQuantity, QuoteModel


class ReimbursementClaim(QuoteModel):
    """An approved eligible amount and its assigned cap accounting date."""

    claim_id: str
    charged_on: date
    eligible_amount: NonnegativeQuantity
    approval_evidence: str


class ReimbursementPeriod(QuoteModel):
    """Reviewed claims for one assignment and accounting period."""

    currency: str = Field(pattern=r"^[A-Z]{3}$")
    starts_on: date
    ends_on: date
    cap: NonnegativeQuantity | None
    prior_use: NonnegativeQuantity
    applicability_evidence: str
    claims: tuple[ReimbursementClaim, ...]

    @model_validator(mode="after")
    def validate_period(self) -> Self:
        """Require a usable cap and unique claims in declared accounting order."""
        dates = [claim.charged_on for claim in self.claims]
        if (
            self.starts_on >= self.ends_on
            or self.prior_use > (self.cap if self.cap is not None else 0)
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
    remaining: Fraction | None


@dataclass(frozen=True)
class ReimbursementLedger:
    """Reviewed accounting period, ordered claim costs and exact total."""

    period: ReimbursementPeriod
    rows: tuple[ReimbursementRow, ...]
    total: Fraction


def cost_reimbursements(
    period: ReimbursementPeriod,
) -> tuple[ReimbursementRow, ...]:
    """Apply the supplied cap to approved expenses in the declared order.

    Supply a null cap only for a reviewed uncapped rule.
    The caller determines coverage, proration, eligible costs and the period
    to charge. A cap alone creates no cost.
    """
    return build_reimbursement_ledger(period).rows


def build_reimbursement_ledger(period: ReimbursementPeriod) -> ReimbursementLedger:
    """Keep the reviewed period and its applicability evidence with the costs."""
    period = ReimbursementPeriod.model_validate(
        {**dict(period), "claims": tuple(dict(claim) for claim in period.claims)},
    )
    remaining = (
        None
        if period.cap is None
        else Fraction(period.cap) - Fraction(period.prior_use)
    )
    rows: list[ReimbursementRow] = []
    for claim in period.claims:
        cost = Fraction(claim.eligible_amount)
        if remaining is not None:
            cost = min(cost, remaining)
            remaining -= cost
        rows.append(ReimbursementRow(claim, cost, remaining))
    return ReimbursementLedger(
        period,
        tuple(rows),
        sum((row.cost for row in rows), Fraction(0)),
    )


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


def sa_consultant_development_caps(
    nominal_half_days_per_week: NonnegativeQuantity,
) -> tuple[Fraction, Fraction]:
    """Return annual and two-year FBT-inclusive limits for a covered consultant.

    Use the reviewed appointment under clause 45.1.2 of the 2022 agreement.
    Eligibility, accumulated balances and approved claims are separate inputs.
    """
    return _consultant_caps(nominal_half_days_per_week, 22000)


def sa_consultant_development_caps_2025(
    nominal_half_days_per_week: NonnegativeQuantity,
    effective_on: date,
) -> tuple[Fraction, Fraction]:
    """Select the expense caps under the reviewed 2025 agreement.

    Coverage as a non-casual consultant and any retrospective adjustment must
    be established separately. The date is the applicable entitlement date.
    """
    if effective_on < date(2025, 4, 14):
        msg = "Date precedes the first 2025 agreement development cap"
        raise ValueError(msg)
    full_annual_cap = 23000 if effective_on >= date(2026, 4, 14) else 22000
    return _consultant_caps(nominal_half_days_per_week, full_annual_cap)


def _consultant_caps(
    nominal_half_days_per_week: NonnegativeQuantity,
    full_annual_cap: int,
) -> tuple[Fraction, Fraction]:
    half_days = Fraction(nominal_half_days_per_week)
    if half_days <= 0:
        msg = "Consultant appointment must have positive nominal half-days"
        raise ValueError(msg)
    full_cap_threshold = 5
    annual_cap = Fraction(full_annual_cap)
    if half_days < full_cap_threshold:
        annual_cap /= 2
    return annual_cap, 2 * annual_cap


class ReimbursementRecoveryDecision(QuoteModel):
    """Reviewed resignation reconciliation for one entitlement period."""

    reimbursed: NonnegativeQuantity
    prorated_entitlement: NonnegativeQuantity
    approved_recovery: NonnegativeQuantity
    decision_evidence: str

    @model_validator(mode="after")
    def validate_recovery(self) -> Self:
        """Limit the employer's decision to the excess reimbursement."""
        excess = max(0, Fraction(self.reimbursed) - Fraction(self.prorated_entitlement))
        if self.approved_recovery > excess:
            msg = "Approved recovery exceeds reimbursement above prorated entitlement"
            raise ValueError(msg)
        return self


def reimbursement_cost_after_recovery(
    decision: ReimbursementRecoveryDecision,
) -> Fraction:
    """Return net expense cost after the supplied reviewed recovery.

    The caller establishes eligibility, proration and the recovery decision.
    The result values that decision without changing claims or payroll.
    """
    decision = ReimbursementRecoveryDecision.model_validate(dict(decision))
    return Fraction(decision.reimbursed) - Fraction(decision.approved_recovery)


def sa_ordinary_study_fee_amount(
    compulsory_tuition: NonnegativeQuantity,
    examination_fees: NonnegativeQuantity,
    *,
    proof_of_passing: bool,
) -> Fraction:
    """Value the ordinary fee route in SA Health HR Manual 7/22 section 7-1-4.

    Supply only reviewed eligible tuition and examination fees. Withdrawal,
    apprenticeship and discretionary assistance require separate review.
    """
    tuition = Fraction(compulsory_tuition)
    exams = Fraction(examination_fees)
    if min(tuition, exams) < 0:
        msg = "Study fees must be nonnegative"
        raise ValueError(msg)
    return tuition + exams if proof_of_passing else Fraction(0)
