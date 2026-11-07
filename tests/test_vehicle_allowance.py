# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Test receipt-based exclusion without converting between units."""

from datetime import UTC, date, datetime
from decimal import Decimal
from fractions import Fraction

import pytest

from src.periodic_allowance import (
    cost_periodic_allowance,
    cost_periodic_allowance_allocations,
)
from src.source_registry import SourceRegistry
from src.unit_quotes import price_units
from src.vehicle_allowance import (
    C24NursingAppointment,
    ExcessVehicleDistance,
    Moca7VehicleAppointment,
    VehicleTravelCase,
    VehicleTravelExclusion,
    c24_nursing_vehicle_level,
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
        award_vehicle_allowance_selected=False,
        review_evidence="Synthetic covered appointment and receipt assessment",
    )
    assert_that(moca7_vehicle_level(appointment) == expected)


@pytest.mark.parametrize(
    ("lower", "upper", "payable", "accrued"),
    [
        ("2600", "5200", Fraction(75), Fraction(100)),
        ("24097", "29260", Fraction(31412, 52), Fraction(38727, 52)),
    ],
)
def test_moca7_vehicle_level_change_across_fortnight(
    lower: str,
    upper: str,
    payable: Fraction,
    accrued: Fraction,
) -> None:
    """Price a reviewed manager receipt change with one nominal denominator."""
    appointment = Moca7VehicleAppointment(
        classification_level=24,
        received_manager_allowance_level=0,
        award_vehicle_allowance_selected=False,
        review_evidence="Synthetic reviewed nonreceipt",
    )
    promoted = appointment.model_copy(
        update={
            "received_manager_allowance_level": 6,
            "review_evidence": "Synthetic reviewed manager receipt",
        },
    )
    conditions = (
        condition("vehicle-1", "fixed_annual", lower, "AUD/year"),
        condition("vehicle-2", "fixed_annual", upper, "AUD/year"),
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
    allocations = (
        (rates, f"vehicle-{moca7_vehicle_level(appointment)}", before),
        (rates, f"vehicle-{moca7_vehicle_level(promoted)}", after),
    )
    parent = period(*before.portions, *after.portions)
    result = cost_periodic_allowance_allocations(parent, allocations)
    assert_that(
        [segment.condition.condition_id for segment in result.segments]
        == ["vehicle-1", "vehicle-2"],
    )
    assert_that(result.payable == payable)
    assert_that(result.accrued == accrued)
    frozen = cost_periodic_allowance_allocations(
        parent,
        (allocations[0], (rates, allocations[0][1], after)),
    )
    assert_that(
        result.payable - frozen.payable == Fraction(int(upper) - int(lower), 208),
    )
    with pytest.raises(ValueError, match="conserve classified hours"):
        cost_periodic_allowance_allocations(period(*before.portions), allocations)


def test_moca7_rejects_concurrent_award_vehicle_allowance() -> None:
    """Clause 11.33.4 excludes concurrent award vehicle allowance."""
    appointment = Moca7VehicleAppointment(
        classification_level=25,
        received_manager_allowance_level=0,
        award_vehicle_allowance_selected=True,
        review_evidence="Synthetic reviewed concurrent selection",
    )
    with pytest.raises(ValueError, match="cannot be selected together"):
        moca7_vehicle_level(appointment)


@pytest.mark.parametrize(("journey", "expected"), [(30, 10), (20, 0), (10, 0)])
def test_excess_vehicle_distance(journey: int, expected: int) -> None:
    """Only comparable distance beyond the usual commute is payable."""
    case = ExcessVehicleDistance(
        journey=quantity(unit="km", quantity=Decimal(journey)),
        normal_commute_km=Decimal(20),
        commute_evidence="Synthetic usual commute",
    )
    payable = case.payable_quantity()
    rates = release(quote(unit="km", amount=Decimal("0.75")))
    assert_that(payable.quantity == Fraction(expected))
    assert_that(price_units(rates, (payable,)).total == Fraction(expected * 3, 4))


def test_excess_vehicle_distance_uses_dated_award_rate() -> None:
    """Retain the quote date across the certified reprint boundary."""
    boundary = date(2026, 9, 1)
    rates = release(
        quote(unit="km", amount=Decimal("0.99"), ends_on=boundary),
        quote(quote_id="new", unit="km", amount=Decimal(1), starts_on=boundary),
    )
    case = ExcessVehicleDistance(
        journey=quantity(unit="km", quantity=Decimal(30), valued_on=date(2026, 8, 31)),
        normal_commute_km=Decimal(20),
        commute_evidence="Synthetic usual commute",
    )
    before = case.payable_quantity()
    later = case.journey.model_copy(
        update={"quote_id": "new", "quantity_id": "later", "valued_on": boundary},
    )
    after = case.model_copy(update={"journey": later}).payable_quantity()
    result = price_units(rates, (before, after))
    assert_that(result.total == Fraction("19.90"))
    with pytest.raises(ValueError, match="date"):
        price_units(rates, (after.model_copy(update={"quote_id": before.quote_id}),))


@pytest.mark.parametrize(("grade", "level"), [("grade_11_band_4", 1), ("grade_12", 2)])
def test_c24_nursing_vehicle_level(grade: str, level: int) -> None:
    """Only reviewed EDON grades map to the recurring allowance bands."""
    appointment = C24NursingAppointment.model_validate(
        {"classification": grade, "review_evidence": "Synthetic EDON review"},
    )
    assert_that(c24_nursing_vehicle_level(appointment) == level)
    rates = condition_release().model_copy(
        update={
            "conditions": (
                condition("vehicle-1", "fixed_annual", "24097", "AUD/year"),
                condition("vehicle-2", "fixed_annual", "29260", "AUD/year"),
            ),
        },
    )
    exposure = period(
        portion("paid-leave", "38", "1", "1"),
        portion("half-pay", "19", "1", "0.5"),
        portion("unpaid", "19", "0", "0"),
    )
    result = cost_periodic_allowance(
        rates,
        f"vehicle-{c24_nursing_vehicle_level(appointment)}",
        exposure,
    )
    annual = 24097 if level == 1 else 29260
    assert_that(result.payable == Fraction(annual * 5, 208))
    with pytest.raises(ValueError, match="classification"):
        c24_nursing_vehicle_level(
            appointment.model_copy(update={"classification": "grade_11_band_3"}),
        )
