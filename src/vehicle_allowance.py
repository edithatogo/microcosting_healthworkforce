# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Price travel after an explicitly evidenced recurring allowance exclusion."""

from dataclasses import dataclass
from fractions import Fraction
from typing import Literal
lazy from datetime import date

from pydantic import Field

from src.unit_quotes import (
    NonnegativeQuantity,
    QuoteModel,
    QuoteQuantity,
    UnitQuoteRelease,
    UnitQuoteResult,
    price_units,
)
lazy from src.source_registry import SourceRecord


class VehicleTravelCase(QuoteModel):
    """Reviewed receipt status for the worker on the travel valuation date."""

    travel: QuoteQuantity
    recurring_allowance_received: bool
    receipt_evidence: str
    receipt_known_on: date


class VehicleTravelExclusion(QuoteModel):
    """Source and citation for an applicable receipt-based exclusion."""

    travel_component: str
    source_id: str
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation: str
    reviewed: bool
    effective_from: date
    effective_to: date
    known_from: date


@dataclass(frozen=True)
class VehicleTravelCost:
    """Retain suppressed cases without pricing their mileage."""

    rule: VehicleTravelExclusion
    suppressed: tuple[VehicleTravelCase, ...]
    prices: UnitQuoteResult


def price_vehicle_travel(
    release: UnitQuoteRelease,
    rule: VehicleTravelExclusion,
    cases: tuple[VehicleTravelCase, ...],
) -> VehicleTravelCost:
    """Exclude mileage when receipt is verified for the same worker and date."""
    release = UnitQuoteRelease.model_validate(release.model_dump())
    rule = VehicleTravelExclusion.model_validate(rule.model_dump())
    if not rule.reviewed:
        msg = "Vehicle travel exclusion requires a reviewed rule"
        raise ValueError(msg)
    if (
        rule.effective_from >= rule.effective_to
        or rule.known_from > release.as_known_on
    ):
        msg = "Vehicle exclusion requires valid dates and a known rule"
        raise ValueError(msg)
    # Preserve exact Fraction quantities while revalidating the nested input.
    cases = tuple(
        VehicleTravelCase.model_validate(dict(case, travel=dict(case.travel)))
        for case in cases
    )
    if len({case.travel.quantity_id for case in cases}) != len(cases):
        msg = "Duplicate vehicle travel quantity identity"
        raise ValueError(msg)
    quotes = {quote.quote_id: quote for quote in release.quotes}
    suppressed: list[VehicleTravelCase] = []
    payable: list[QuoteQuantity] = []
    for case in cases:
        travel = case.travel
        if not rule.effective_from <= travel.valued_on < rule.effective_to:
            msg = "Vehicle exclusion does not cover the travel date"
            raise ValueError(msg)
        if case.receipt_known_on > release.as_known_on:
            msg = "Vehicle receipt evidence exceeds the release knowledge cutoff"
            raise ValueError(msg)
        quote = quotes.get(travel.quote_id)
        if quote is not None and quote.component != rule.travel_component:
            msg = "Vehicle travel quote does not match the reviewed travel component"
            raise ValueError(msg)
        source = release.sources.require_applicable(
            rule.source_id,
            travel.valued_on,
            release.jurisdiction,
            release.employer,
            release.classification,
        )
        if source.sha256 != rule.source_sha256 or travel.unit != "km":
            msg = "Vehicle travel requires a matching source hash and kilometre units"
            raise ValueError(msg)
        _require_known_source(source, release.as_known_on)
        if case.recurring_allowance_received:
            suppressed.append(case)
        else:
            payable.append(travel)
    return VehicleTravelCost(
        rule,
        tuple(suppressed),
        price_units(release, tuple(payable)),
    )


def _require_known_source(source: SourceRecord, cutoff: date) -> None:
    if source.retrieved_at is None or source.retrieved_at.date() > cutoff:
        msg = "Vehicle exclusion source exceeds the release knowledge cutoff"
        raise ValueError(msg)


class Moca7VehicleAppointment(QuoteModel):
    """Reviewed covered SMO or MPPP appointment for one valuation."""

    classification_level: int = Field(ge=13, le=29)
    received_manager_allowance_level: int = Field(ge=0)
    award_vehicle_allowance_selected: bool
    review_evidence: str


def moca7_vehicle_level(appointment: Moca7VehicleAppointment) -> Literal[1, 2]:
    """Select the SES equivalent under MOCA7 clause 11.33.2.

    Zero manager allowance level means reviewed nonreceipt. The caller
    establishes appointment coverage and selects the dated amount separately.
    """
    appointment = Moca7VehicleAppointment.model_validate(appointment.model_dump())
    if appointment.award_vehicle_allowance_selected:
        msg = "MOCA7 and award vehicle allowances cannot be selected together"
        raise ValueError(msg)
    upper_classification_start = 25
    manager_override_start = 6
    if (
        appointment.classification_level >= upper_classification_start
        or appointment.received_manager_allowance_level >= manager_override_start
    ):
        return 2
    return 1


class ExcessVehicleDistance(QuoteModel):
    """Comparable journey distances for independently reviewed excess travel."""

    journey: QuoteQuantity
    normal_commute_km: NonnegativeQuantity
    commute_evidence: str

    def payable_quantity(self) -> QuoteQuantity:
        """Subtract the usual commute and preserve the dated quote identity."""
        case = ExcessVehicleDistance.model_validate(
            dict(self, journey=dict(self.journey)),
        )
        if case.journey.unit != "km":
            msg = "Excess vehicle distance requires kilometre units"
            raise ValueError(msg)
        excess = Fraction(case.journey.quantity) - Fraction(case.normal_commute_km)
        return QuoteQuantity.model_validate(
            dict(
                case.journey,
                quantity=max(Fraction(0), excess),
                basis=(
                    f"{case.journey.basis}. "
                    f"Usual commute evidence {case.commute_evidence}"
                ),
            ),
        )


class C24NursingAppointment(QuoteModel):
    """Reviewed Queensland Health EDON appointment covered by C24."""

    classification: Literal["grade_11_band_4", "grade_12"]
    review_evidence: str


def c24_nursing_vehicle_level(appointment: C24NursingAppointment) -> Literal[1, 2]:
    """Select the SES band for a reviewed EDON appointment."""
    appointment = C24NursingAppointment.model_validate(appointment.model_dump())
    return 1 if appointment.classification == "grade_11_band_4" else 2
