# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Approved expense costs and remaining cap reconcile exactly."""

from datetime import date
from decimal import Decimal
from fractions import Fraction

import pytest

from src.reimbursement import (
    ReimbursementCarryDecision,
    ReimbursementClaim,
    ReimbursementPeriod,
    cost_reimbursements,
    reimbursement_carry_amount,
)
from tests.checks import assert_that


def test_reimbursements_cost_only_approved_expenses_within_remaining_cap() -> None:
    """A partially used cap can limit one claim and exhaust the next."""
    start = date(2026, 7, 1)
    end = date(2027, 7, 1)
    claims = tuple(
        ReimbursementClaim(
            claim_id=f"claim-{index}",
            charged_on=start,
            eligible_amount=Decimal(amount),
            approval_evidence="Synthetic approved claim",
        )
        for index, amount in enumerate(("20.01", "70", "5"))
    )
    period = ReimbursementPeriod(
        currency="AUD",
        starts_on=start,
        ends_on=end,
        cap=Decimal("100.05"),
        prior_use=Decimal(25),
        applicability_evidence="Synthetic reviewed period",
        claims=claims,
    )
    rows = cost_reimbursements(period)
    assert_that([r.cost for r in rows] == [Fraction("20.01"), Fraction("55.04"), 0])
    assert_that([r.remaining for r in rows] == [Fraction("55.04"), 0, 0])
    assert_that(cost_reimbursements(period.model_copy(update={"claims": ()})) == ())
    for invalid in (
        (claims[0], claims[0]),
        (claims[0].model_copy(update={"charged_on": end}),),
    ):
        with pytest.raises(ValueError, match="Invalid reimbursement period"):
            cost_reimbursements(period.model_copy(update={"claims": invalid}))


def test_carry_uses_reviewed_balances_and_remaining_ceiling() -> None:
    """A renewed decision can admit the prior balance up to the ceiling."""
    decision = ReimbursementCarryDecision(
        current_remaining=Fraction(100, 3),
        prior_remaining=Decimal(40),
        carry_limit=Decimal(50),
        eligible_balances="current",
        decision_evidence="Synthetic reviewed allocation",
    )
    assert_that(reimbursement_carry_amount(decision) == Fraction(100, 3))
    renewed = decision.model_copy(update={"eligible_balances": "current_and_prior"})
    assert_that(reimbursement_carry_amount(renewed) == Fraction(50))
    expired = decision.model_copy(update={"eligible_balances": "none"})
    assert_that(reimbursement_carry_amount(expired) == 0)
    with pytest.raises(ValueError, match="carry_limit"):
        reimbursement_carry_amount(decision.model_copy(update={"carry_limit": -1}))


def test_exact_carry_can_fund_the_next_period() -> None:
    """A rational carry remains exact when used by a subsequent claim."""
    carry = reimbursement_carry_amount(
        ReimbursementCarryDecision(
            current_remaining=Fraction(100, 3),
            prior_remaining=Decimal(0),
            carry_limit=Decimal(50),
            eligible_balances="current",
            decision_evidence="Synthetic year-end review",
        ),
    )
    day = date(2027, 7, 1)
    claim = ReimbursementClaim(
        claim_id="next-year",
        charged_on=day,
        eligible_amount=Decimal(150),
        approval_evidence="Synthetic approved expense",
    )
    period = ReimbursementPeriod(
        currency="AUD",
        starts_on=day,
        ends_on=date(2028, 7, 1),
        cap=100 + carry,
        prior_use=Fraction(1, 3),
        applicability_evidence="Synthetic reviewed cap including carry",
        claims=(claim,),
    )
    (row,) = cost_reimbursements(period)
    assert_that(row.cost == Fraction(133))
    assert_that(row.remaining == 0)
