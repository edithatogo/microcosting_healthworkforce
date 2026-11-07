# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Test receipt-based exclusion without converting between units."""

from datetime import UTC, date, datetime
from decimal import Decimal
from fractions import Fraction

import pytest

from src.periodic_allowance import cost_periodic_allowance
from src.source_registry import SourceRegistry
from src.vehicle_allowance import (
    Moca7VehicleAppointment,
    VehicleTravelCase,
    VehicleTravelExclusion,
    moca7_vehicle_level,
    price_vehicle_travel,
)
from tests.checks import assert_that
from tests.test_conditions import condition
from tests.test_periodic_allowance import period, portion
from tests.test_periodic_allowance import release as condition_release
from tests.test_unit_quotes import quantity, quote, release


def test_receipt_excludes_travel_before_pricing() -> None:
    """Only a case with explicit nonreceipt contributes mileage cost."""
    rates = release(quote(unit="km", component="award-travel", amount=Decimal("0.75")))
    rule = VehicleTravelExclusion(
        travel_component="award-travel",
        source_id="synthetic-award-1",
        source_sha256="a" * 64,
        citation="Synthetic exclusion clause",
        reviewed=True,
        effective_from=date(2026, 1, 1),
        effective_to=date(2027, 1, 1),
        known_from=date(2026, 1, 1),
    )
    paid = VehicleTravelCase(
        travel=quantity(unit="km", quantity=Decimal(20)),
        recurring_allowance_received=False,
        receipt_known_on=date(2026, 2, 1),
        receipt_evidence="Synthetic reviewed nonreceipt",
    )
    suppressed = VehicleTravelCase(
        travel=quantity(unit="km", quote_id="unused", quantity_id="suppressed"),
        recurring_allowance_received=True,
        receipt_known_on=date(2026, 2, 1),
        receipt_evidence="Synthetic reviewed receipt",
    )
    result = price_vehicle_travel(rates, rule, (paid, suppressed))
    assert_that(result.prices.total == Fraction(15))
    assert_that(result.suppressed == (suppressed,))
    fractional = paid.model_copy(
        update={"travel": quantity(unit="km", quantity=Fraction(1, 3))},
    )
    assert_that(
        price_vehicle_travel(rates, rule, (fractional,)).prices.total == Fraction(1, 4),
    )
    with pytest.raises(ValueError, match="matching source hash"):
        price_vehicle_travel(
            rates,
            rule.model_copy(update={"source_sha256": "b" * 64}),
            (suppressed,),
        )
    with pytest.raises(ValueError, match="knowledge cutoff"):
        price_vehicle_travel(
            rates,
            rule,
            (paid.model_copy(update={"receipt_known_on": date(2026, 2, 2)}),),
        )
    with pytest.raises(ValueError, match="reviewed travel component"):
        price_vehicle_travel(
            rates,
            rule.model_copy(update={"travel_component": "unrelated"}),
            (paid,),
        )
    with pytest.raises(ValueError, match="does not cover the travel date"):
        price_vehicle_travel(
            rates,
            rule.model_copy(update={"effective_to": paid.travel.valued_on}),
            (paid,),
        )
    with pytest.raises(ValueError, match="Duplicate vehicle travel quantity identity"):
        price_vehicle_travel(
            rates,
            rule,
            (paid, paid.model_copy(update={"recurring_allowance_received": True})),
        )
    with pytest.raises(ValueError, match="kilometre units"):
        price_vehicle_travel(
            rates,
            rule,
            (suppressed.model_copy(update={"travel": quantity(unit="annum")}),),
        )

    source = rates.sources.records[0]
    late_source = source.model_copy(
        update={
            "source_id": "late-rule",
            "retrieved_at": datetime(2026, 2, 2, tzinfo=UTC),
        },
    )
    late_release = rates.model_copy(
        update={"sources": SourceRegistry(records=(source, late_source))},
    )
    with pytest.raises(ValueError, match="exclusion source exceeds"):
        price_vehicle_travel(
            late_release,
            rule.model_copy(update={"source_id": "late-rule"}),
            (suppressed,),
        )


@pytest.mark.parametrize(
    ("classification", "manager_level", "expected"),
    [(13, 0, 1), (24, 5, 1), (24, 6, 2), (25, 0, 2), (29, 0, 2)],
)
def test_moca7_vehicle_level(
    classification: int,
    manager_level: int,
    expected: int,
) -> None:
    """Apply the grade boundary and reviewed manager receipt exception."""
    appointment = Moca7VehicleAppointment(
        classification_level=classification,
        received_manager_allowance_level=manager_level,
        review_evidence="Synthetic covered appointment and receipt assessment",
    )
    assert_that(moca7_vehicle_level(appointment) == expected)


def test_moca7_vehicle_level_change_across_fortnight() -> None:
    """Price a reviewed manager receipt change with one nominal denominator."""
    appointment = Moca7VehicleAppointment(
        classification_level=24,
        received_manager_allowance_level=0,
        review_evidence="Synthetic reviewed nonreceipt",
    )
    promoted = appointment.model_copy(
        update={
            "received_manager_allowance_level": 6,
            "review_evidence": "Synthetic reviewed manager receipt",
        },
    )
    conditions = (
        condition("vehicle-1", "fixed_annual", "2600", "AUD/year"),
        condition("vehicle-2", "fixed_annual", "5200", "AUD/year"),
    )
    rates = condition_release().model_copy(update={"conditions": conditions})
    boundary = date(2026, 6, 8)
    before = period(portion("ordinary", "38", "1", "1")).model_copy(
        update={"ends_on": boundary},
    )
    after = period(
        portion("half-pay", "19", "1", "0.5"),
        portion("unpaid", "19", "0", "0"),
    ).model_copy(update={"starts_on": boundary})
    first = cost_periodic_allowance(
        rates,
        f"vehicle-{moca7_vehicle_level(appointment)}",
        before,
    )
    second = cost_periodic_allowance(
        rates,
        f"vehicle-{moca7_vehicle_level(promoted)}",
        after,
    )
    assert_that(first.condition.condition_id == "vehicle-1")
    assert_that(second.condition.condition_id == "vehicle-2")
    assert_that(first.payable + second.payable == Fraction(75))
    assert_that(first.accrued + second.accrued == Fraction(100))
