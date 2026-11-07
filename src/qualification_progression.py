# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Validate a proposed pay point against a reviewed qualification barrier."""

from dataclasses import dataclass
from fractions import Fraction
lazy from collections.abc import Mapping
lazy from datetime import date

from pydantic import Field

from src.advancement_effective import AdvancementRule
from src.source_registry import SourceRecord, SourceRegistry
from src.unit_quotes import (
    QuoteModel,
    QuoteQuantity,
    UnitQuoteRelease,
    UnitQuoteResult,
    price_units,
)


class ProgressionBarrier(AdvancementRule):
    """An applicable source rule with explicit alternative qualification codes."""

    first_gated_year: int = Field(ge=2)
    accepted_codes: frozenset[str] = Field(min_length=1)


class ProgressionRequest(QuoteModel):
    """A proposed service year and reviewed qualifications at the valuation date."""

    valued_on: date
    proposed_year: int = Field(ge=1)
    qualification_codes: frozenset[str]
    known_on: date
    evidence_id: str
    reviewed: bool


class WeeklyQualificationAllowance(QuoteModel):
    """Reviewed allowance mapping and pay-point condition for this classification."""

    quote_id: str
    accepted_codes: frozenset[str] = Field(min_length=1)
    minimum_year_in_receipt: int | None = Field(default=None, ge=1)
    year_in_receipt: int | None = Field(default=None, ge=1)


@dataclass(frozen=True)
class ProgressionDecision:
    """Retain both the assessed request and its exact source edition."""

    barrier: ProgressionBarrier
    request: ProgressionRequest
    source: SourceRecord
    permitted: bool


def assess_progression(
    barrier: ProgressionBarrier,
    request: ProgressionRequest,
    sources: SourceRegistry,
) -> ProgressionDecision:
    """Assess one barrier before selecting a pay quote for the proposed year."""
    barrier = ProgressionBarrier.model_validate(barrier.model_dump())
    request = ProgressionRequest.model_validate(request.model_dump())
    sources = SourceRegistry.model_validate(sources.model_dump())
    if not barrier.reviewed or not request.reviewed:
        msg = "Progression requires reviewed rule and request evidence"
        raise ValueError(msg)
    if request.known_on > barrier.as_known_on:
        msg = "Progression evidence exceeds the knowledge horizon"
        raise ValueError(msg)
    if any(
        not code.strip()
        for code in barrier.accepted_codes | request.qualification_codes
    ):
        msg = "Qualification codes must be nonblank"
        raise ValueError(msg)
    source = sources.require_applicable(
        barrier.source_id,
        request.valued_on,
        barrier.jurisdiction,
        barrier.employer,
        barrier.classification,
    )
    if (
        source.sha256 != barrier.source_sha256
        or source.retrieved_at is None
        or source.retrieved_at.date() > barrier.as_known_on
    ):
        msg = "Progression source must match the held and known edition"
        raise ValueError(msg)
    permitted = request.proposed_year < barrier.first_gated_year or bool(
        request.qualification_codes & barrier.accepted_codes,
    )
    return ProgressionDecision(barrier, request, source, permitted)


def price_progression_week(
    release: UnitQuoteRelease,
    barrier: ProgressionBarrier,
    request: ProgressionRequest,
    quotes_by_year: Mapping[int, str],
    *,
    allowance: WeeklyQualificationAllowance | None = None,
) -> tuple[ProgressionDecision, UnitQuoteResult]:
    """Price one week using the caller's reviewed mapping of years to wage quotes."""
    if (
        barrier.jurisdiction,
        barrier.employer,
        barrier.classification,
        barrier.as_known_on,
    ) != (
        release.jurisdiction,
        release.employer,
        release.classification,
        release.as_known_on,
    ):
        msg = "Progression and price release must share scope and knowledge date"
        raise ValueError(msg)
    decision = assess_progression(barrier, request, release.sources)
    if not decision.permitted:
        msg = "Proposed service year requires a qualifying credential"
        raise ValueError(msg)
    quote_id = quotes_by_year.get(decision.request.proposed_year)
    if quote_id is None:
        msg = "Proposed service year requires a mapped weekly wage quote"
        raise ValueError(msg)
    quantity = QuoteQuantity(
        quantity_id="progression-week",
        quote_id=quote_id,
        unit="week",
        quantity=Fraction(1),
        valued_on=decision.request.valued_on,
        quantity_kind="analyst_assumption",
        basis=decision.request.evidence_id,
    )
    quantities = [quantity]
    if allowance is not None:
        allowance = WeeklyQualificationAllowance.model_validate(allowance.model_dump())
        if allowance.quote_id == quote_id or any(
            not code.strip() for code in allowance.accepted_codes
        ):
            msg = "Allowance requires a distinct quote and nonblank qualification codes"
            raise ValueError(msg)
        if (
            allowance.minimum_year_in_receipt is not None
            and allowance.year_in_receipt is None
        ):
            msg = "Allowance requires the reviewed service year in receipt"
            raise ValueError(msg)
        meets_year = allowance.minimum_year_in_receipt is None or (
            allowance.year_in_receipt is not None
            and allowance.year_in_receipt >= allowance.minimum_year_in_receipt
        )
        if (
            meets_year
            and decision.request.qualification_codes & allowance.accepted_codes
        ):
            quantities.append(
                quantity.model_copy(
                    update={
                        "quantity_id": "qualification-allowance-week",
                        "quote_id": allowance.quote_id,
                    },
                ),
            )
    return decision, price_units(release, tuple(quantities))
