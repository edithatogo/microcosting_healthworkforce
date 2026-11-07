# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Price travel after an explicitly evidenced recurring allowance exclusion."""

from dataclasses import dataclass
lazy from datetime import date

from pydantic import Field

from src.unit_quotes import (
    QuoteModel,
    QuoteQuantity,
    UnitQuoteRelease,
    UnitQuoteResult,
    price_units,
)


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
    cases = tuple(VehicleTravelCase.model_validate(c.model_dump()) for c in cases)
    if len({case.travel.quantity_id for case in cases}) != len(cases):
        msg = "Duplicate vehicle travel quantity identity"
        raise ValueError(msg)
    quotes = {quote.quote_id: quote for quote in release.quotes}
    suppressed: list[VehicleTravelCase] = []
    payable: list[QuoteQuantity] = []
    for case in cases:
        travel = case.travel
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
        if case.recurring_allowance_received:
            suppressed.append(case)
        else:
            payable.append(travel)
    return VehicleTravelCost(
        rule,
        tuple(suppressed),
        price_units(release, tuple(payable)),
    )
