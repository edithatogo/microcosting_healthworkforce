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
    ReimbursementRecoveryDecision,
    cost_reimbursements,
    reimbursement_carry_amount,
    reimbursement_cost_after_recovery,
    sa_consultant_development_caps,
    sa_consultant_development_caps_2025,
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


def test_sa_consultant_development_caps_at_half_day_boundary() -> None:
    """The lower bracket ends at exactly five nominal half-days."""
    assert_that(
        sa_consultant_development_caps(Decimal("4.99"))
        == (Fraction(11000), Fraction(22000)),
    )
    assert_that(
        sa_consultant_development_caps(Decimal(5))
        == (Fraction(22000), Fraction(44000)),
    )
    with pytest.raises(ValueError, match="positive nominal half-days"):
        sa_consultant_development_caps(Decimal(0))


def test_sa_development_claim_respects_reviewed_two_year_headroom() -> None:
    """The annual allocation and carry together fit the two-year ceiling."""
    annual_cap, two_year_cap = sa_consultant_development_caps(Decimal(5))
    carry = reimbursement_carry_amount(
        ReimbursementCarryDecision(
            current_remaining=Decimal(18000),
            prior_remaining=Decimal(9000),
            carry_limit=two_year_cap - annual_cap,
            eligible_balances="current_and_prior",
            decision_evidence="Synthetic reviewed eligible balances",
        ),
    )
    start = date(2023, 7, 1)
    (row,) = cost_reimbursements(
        ReimbursementPeriod(
            currency="AUD",
            starts_on=start,
            ends_on=date(2024, 7, 1),
            cap=annual_cap + carry,
            prior_use=Decimal("1500.25"),
            applicability_evidence="Synthetic reviewed cap and carry allocation",
            claims=(
                ReimbursementClaim(
                    claim_id="approved-development-expense",
                    charged_on=start,
                    eligible_amount=Decimal(43000),
                    approval_evidence="Synthetic FBT-inclusive approved amount",
                ),
            ),
        ),
    )
    assert_that(carry == Fraction(22000))
    assert_that(row.cost == Fraction("42499.75"))
    assert_that(row.remaining == 0)


def test_sa_successor_development_cap_effective_dates() -> None:
    """The successor raises both brackets at its operative date."""
    select = sa_consultant_development_caps_2025
    with pytest.raises(ValueError, match="precedes"):
        select(Decimal(5), date(2025, 4, 13))
    for day in (date(2025, 4, 14), date(2026, 4, 13)):
        assert_that(select(Decimal(5), day) == (22000, 44000))
    boundary = date(2026, 4, 14)
    assert_that(select(Decimal(5), boundary) == (23000, 46000))
    assert_that(select(Decimal("4.99"), boundary) == (11500, 23000))


def test_reimbursement_recovery_is_discretionary_and_limited_to_excess() -> None:
    """An employer can choose a smaller recovery than the eligible excess."""
    decision = ReimbursementRecoveryDecision(
        reimbursed=Decimal("14000.25"),
        prorated_entitlement=Decimal(11000),
        approved_recovery=Decimal("2500.10"),
        decision_evidence="Synthetic approved resignation reconciliation",
    )
    assert_that(reimbursement_cost_after_recovery(decision) == Fraction("11500.15"))
    declined = decision.model_copy(update={"approved_recovery": Decimal(0)})
    assert_that(reimbursement_cost_after_recovery(declined) == Fraction("14000.25"))
    excess = decision.model_copy(update={"approved_recovery": Decimal("3000.26")})
    with pytest.raises(ValueError, match="exceeds reimbursement"):
        reimbursement_cost_after_recovery(excess)
