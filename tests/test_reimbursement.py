# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Approved expense costs and remaining cap reconcile exactly."""

from datetime import date
from decimal import Decimal
from fractions import Fraction

import pytest

from src.reimbursement import (
    ReimbursementClaim,
    ReimbursementPeriod,
    cost_reimbursements,
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
