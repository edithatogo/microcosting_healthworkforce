# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Test receipt-based exclusion without converting between units."""

from datetime import UTC, date, datetime
from decimal import Decimal
from fractions import Fraction

import pytest

from src.source_registry import SourceRegistry
from src.vehicle_allowance import (
    VehicleTravelCase,
    VehicleTravelExclusion,
    price_vehicle_travel,
)
from tests.checks import assert_that
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
