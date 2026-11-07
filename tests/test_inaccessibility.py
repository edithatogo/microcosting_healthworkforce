# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Verify the two standard first-payment milestones with synthetic inputs."""

from datetime import date
from decimal import Decimal
from fractions import Fraction
from typing import Literal

import pytest

from src.inaccessibility import (
    InaccessibilityCategoryPayment,
    InaccessibilityFirstPayment,
    InaccessibilityRecurringPayment,
    InaccessibilityRotationPayment,
    price_inaccessibility_category_payments,
    price_inaccessibility_first_payment,
    price_inaccessibility_recurring_payment,
    price_inaccessibility_rotation_payment,
)
from tests.checks import assert_that
from tests.test_unit_quotes import quote, release


@pytest.mark.parametrize(
    ("category", "threshold", "amount"),
    [(3, 6, 300), (4, 12, 600)],
)
def test_first_payment_threshold_and_proration(
    category: Literal[3, 4],
    threshold: int,
    amount: int,
) -> None:
    """Check the month before qualification, the boundary and prior payment."""
    rates = release(
        quote(
            component=f"inaccessibility-category-{category}",
            unit="annum",
            amount=Decimal(1200),
        ),
    )
    request = InaccessibilityFirstPayment(
        payment_id="synthetic-first-payment",
        category=category,
        completed_eligible_months=threshold,
        annual_quote_id="period-1",
        valued_on=date(2026, 2, 1),
        service_assessed_through=date(2026, 1, 31),
        employment_fraction=Decimal("0.5"),
        first_payment_already_paid=False,
        review_evidence="Synthetic single-category service and payment history",
    )
    assert_that(
        price_inaccessibility_first_payment(rates, request).total == Fraction(amount),
    )
    assert_that(
        price_inaccessibility_first_payment(rates, request).rows[0].quantity.quantity_id
        == request.payment_id,
    )
    early = request.model_copy(update={"completed_eligible_months": threshold - 1})
    paid = request.model_copy(update={"first_payment_already_paid": True})
    assert_that(price_inaccessibility_first_payment(rates, early).total == 0)
    assert_that(price_inaccessibility_first_payment(rates, paid).total == 0)


def test_first_payment_requires_applicable_annual_component_quote() -> None:
    """Reject unrelated or expired amounts even when the milestone is unmet."""
    request = InaccessibilityFirstPayment(
        payment_id="synthetic-first-payment",
        category=1,
        completed_eligible_months=5,
        annual_quote_id="period-1",
        valued_on=date(2026, 2, 1),
        service_assessed_through=date(2026, 1, 31),
        employment_fraction=Decimal(1),
        first_payment_already_paid=False,
        review_evidence="Synthetic service history",
    )
    with pytest.raises(ValueError, match="inaccessibility category"):
        price_inaccessibility_first_payment(
            release(quote(unit="annum")),
            request,
        )
    wrong_category = quote(component="inaccessibility-category-2", unit="annum")
    with pytest.raises(ValueError, match="inaccessibility category"):
        price_inaccessibility_first_payment(release(wrong_category), request)
    expired = quote(
        component="inaccessibility-category-1",
        unit="annum",
        ends_on=request.valued_on,
    )
    with pytest.raises(ValueError, match="outside the selected quote"):
        price_inaccessibility_first_payment(release(expired), request)


def test_recurring_payment_requires_complete_unpaid_service() -> None:
    """A half-time eligible quarter pays one eighth of the annual benefit."""
    rates = release(
        quote(
            component="inaccessibility-category-7",
            unit="annum",
            amount=Decimal(1200),
        ),
    )
    request = InaccessibilityRecurringPayment(
        category=7,
        annual_quote_id="period-1",
        valued_on=date(2026, 2, 1),
        service_assessed_through=date(2026, 1, 31),
        employment_fraction=Decimal("0.5"),
        payment_id="synthetic-quarter",
        initial_milestone_met=True,
        instalment_service_complete=True,
        instalment_already_paid=False,
        review_evidence="Synthetic quarterly service and payment history",
    )
    result = price_inaccessibility_recurring_payment(rates, request)
    assert_that(result.total == Fraction(150))
    assert_that(result.rows[0].quantity.quantity_id == request.payment_id)
    with pytest.raises(ValueError, match="assessment cannot follow"):
        price_inaccessibility_recurring_payment(
            rates,
            request.model_copy(update={"service_assessed_through": date(2026, 2, 2)}),
        )
    for change in (
        {"initial_milestone_met": False},
        {"instalment_service_complete": False},
        {"instalment_already_paid": True},
    ):
        assert_that(
            price_inaccessibility_recurring_payment(
                rates,
                request.model_copy(update=change),
            ).total
            == 0,
        )


def test_vocational_rotation_exception_uses_reviewed_proration() -> None:
    """Four eligible months qualify under the reviewed rotation exception."""
    rates = release(
        quote(
            component="inaccessibility-category-1",
            unit="annum",
            amount=Decimal(1200),
        ),
    )
    request = InaccessibilityRotationPayment(
        category=1,
        annual_quote_id="period-1",
        valued_on=date(2026, 2, 1),
        employment_fraction=Decimal("0.5"),
        payment_id="rotation-2025",
        service_year=2025,
        service_assessed_through=date(2025, 12, 31),
        completed_eligible_months=4,
        recognised_vocational_rmo=True,
        reviewed_annual_fraction=Fraction(1, 3),
        payment_already_paid=False,
        review_evidence="Synthetic reviewed rotation history and proration",
    )
    payment = price_inaccessibility_rotation_payment(rates, request)
    assert_that(payment.total == Fraction(200))
    for change in (
        {"completed_eligible_months": 3},
        {"recognised_vocational_rmo": False},
        {"payment_already_paid": True},
    ):
        result = price_inaccessibility_rotation_payment(
            rates,
            request.model_copy(update=change),
        )
        assert_that(result.total == 0)
    with pytest.raises(ValueError, match="service year and by valuation"):
        price_inaccessibility_rotation_payment(
            rates,
            request.model_copy(update={"valued_on": date(2025, 12, 30)}),
        )


def test_reviewed_category_payments_use_separate_quotes() -> None:
    """Retain category rows and apply employment proration once."""
    rates = release(
        quote(
            component="inaccessibility-category-1", unit="annum", amount=Decimal(1200),
        ),
        quote(
            quote_id="category-4",
            component="inaccessibility-category-4",
            unit="annum",
            amount=Decimal(600),
            starts_on=date(2026, 3, 1),
        ),
    )
    first = InaccessibilityCategoryPayment(
        category=1,
        payment_id="category-1-payment",
        annual_quote_id="period-1",
        valued_on=date(2026, 2, 1),
        service_assessed_through=date(2026, 1, 31),
        employment_fraction=Decimal("0.5"),
        reviewed_annual_fraction=Fraction(1, 3),
        review_evidence="Synthetic reviewed concurrent category share",
    )
    second = InaccessibilityCategoryPayment.model_validate(
        dict(
            first,
            category=4,
            payment_id="category-4-payment",
            annual_quote_id="category-4",
            valued_on=date(2026, 3, 1),
        ),
    )
    result = price_inaccessibility_category_payments(rates, (first, second))
    assert_that([row.cost for row in result.rows] == [200, 100])
    assert_that(result.total == Fraction(300))
    with pytest.raises(ValueError, match="Duplicate quantity identity"):
        price_inaccessibility_category_payments(rates, (first, first))
    with pytest.raises(ValueError, match="inaccessibility category"):
        price_inaccessibility_category_payments(
            rates,
            (second.model_copy(update={"annual_quote_id": "period-1"}),),
        )
    with pytest.raises(ValueError, match="assessment cannot follow"):
        price_inaccessibility_category_payments(
            rates,
            (
                first.model_copy(
                    update={"service_assessed_through": date(2026, 2, 2)},
                ),
                second,
            ),
        )
    with pytest.raises(ValueError, match="outside the selected quote"):
        price_inaccessibility_category_payments(
            rates,
            (second.model_copy(update={"valued_on": date(2026, 2, 28)}),),
        )
