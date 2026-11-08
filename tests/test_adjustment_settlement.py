# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Check exact settlement and rejection of overlapping payroll credits."""

from datetime import date
from decimal import Decimal
from fractions import Fraction

import pytest

from src.adjustment_settlement import (
    AdjustmentLine,
    AdjustmentSettlement,
    reconcile_adjustment,
)
from src.capped_overtime import DailyHistory, cost_capped_daily_overtime
from tests.checks import assert_that
from tests.test_capped_overtime import activity, release, rule


def test_settlement_retains_signed_lines_and_separate_cash_date() -> None:
    """Reconcile reviewed credits without treating a future payment as observed."""
    line = AdjustmentLine(
        line_id="first",
        component="salary",
        starts_on=date(2026, 1, 1),
        ends_on=date(2026, 1, 15),
        entitled=Decimal("110.05"),
        credited=Decimal("108.01"),
        entitlement_evidence="synthetic entitlement",
        credit_evidence="synthetic credit",
    )
    next_line = line.model_copy(
        update={
            "line_id": "second",
            "starts_on": date(2026, 1, 15),
            "ends_on": date(2026, 1, 29),
            "credited": Decimal("111.05"),
        },
    )
    request = AdjustmentSettlement(
        case_id="synthetic",
        currency="AUD",
        crystallised_on=date(2026, 3, 1),
        reviewed_on=date(2026, 3, 2),
        as_known_on=date(2026, 3, 3),
        planned_payment_on=date(2026, 4, 1),
        review_evidence="synthetic review",
        lines=(line, next_line),
    )
    result = reconcile_adjustment(request)
    assert_that(result.differences == (Fraction(51, 25), Fraction(-1)))
    assert_that(result.net_difference == Fraction(26, 25))
    assert_that(result.request == request)
    duplicate = next_line.model_copy(update={"line_id": " first "})
    with pytest.raises(ValueError, match="Duplicate adjustment line identity"):
        reconcile_adjustment(
            request.model_copy(update={"lines": (line, duplicate)}),
        )
    overlapping = line.model_copy(update={"line_id": "copy", "component": " salary "})
    with pytest.raises(ValueError, match="Overlapping"):
        reconcile_adjustment(
            request.model_copy(update={"lines": (line, overlapping)}),
        )


def test_pharmacy_transition_preserves_components_and_effective_boundary() -> None:
    """Use reviewed counterfactual and credited amounts for the transition."""
    market = AdjustmentLine(
        line_id="market",
        component="pharmacy-market",
        starts_on=date(2026, 2, 6),
        ends_on=date(2026, 5, 13),
        entitled=Decimal("150.25"),
        credited=Decimal("100.10"),
        entitlement_evidence="synthetic amended market calculation",
        credit_evidence="synthetic prior market payment",
    )
    retention = market.model_copy(
        update={
            "line_id": "retention",
            "component": "pharmacy-retention",
            "entitled": Decimal("110.10"),
            "credited": Decimal("120.25"),
        },
    )
    result = reconcile_adjustment(
        AdjustmentSettlement(
            case_id="synthetic-pharmacy-transition",
            currency="AUD",
            crystallised_on=date(2026, 5, 13),
            reviewed_on=date(2026, 5, 14),
            as_known_on=date(2026, 5, 14),
            planned_payment_on=None,
            review_evidence="synthetic reviewed matched transition window",
            lines=(market, retention),
        ),
    )
    assert_that(result.differences == (Fraction("50.15"), Fraction("-10.15")))
    assert_that(result.net_difference == Fraction(40))
    assert_that(result.request.planned_payment_on is None)


def test_time_off_cash_settlement_uses_entitlement_not_base_adjustment() -> None:
    """Settle the cash credit while retaining the time-off hours separately."""
    shift = activity()
    overtime = cost_capped_daily_overtime(
        release(),
        rule().model_copy(update={"time_off_cash_multiplier": Decimal("1.5")}),
        shift,
        "UTC",
        DailyHistory(prior_hours=Decimal(0), complete=True),
    )
    entitled = Decimal(240)
    assert_that(overtime.time_off_cash == Fraction(entitled))
    assert_that(overtime.adjustments[0].adjustment == Fraction(40))
    assert_that(overtime.time_off_hours == Fraction(4))
    worked_on = shift.starts_at.date()
    result = reconcile_adjustment(
        AdjustmentSettlement(
            case_id="synthetic-holiday",
            currency="AUD",
            crystallised_on=worked_on,
            reviewed_on=worked_on,
            as_known_on=worked_on,
            planned_payment_on=None,
            review_evidence="synthetic payroll review",
            lines=(
                AdjustmentLine(
                    line_id="holiday-cash",
                    component="overtime cash",
                    starts_on=worked_on,
                    ends_on=date(2026, 6, 3),
                    entitled=entitled,
                    credited=Decimal(210),
                    entitlement_evidence="synthetic time-off cash entitlement",
                    credit_evidence="synthetic payroll posting",
                ),
            ),
        ),
    )
    assert_that(result.net_difference == Fraction(30))
