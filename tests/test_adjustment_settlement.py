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
from tests.checks import assert_that


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
    with pytest.raises(ValueError, match="Overlapping"):
        reconcile_adjustment(
            request.model_copy(
                update={"lines": (line, line.model_copy(update={"line_id": "copy"}))},
            ),
        )
