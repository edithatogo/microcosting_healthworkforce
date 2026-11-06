# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Direct unit-matched snapshot and dated-event pricing with exact arithmetic.

Quantities are explicit supplied facts or assumptions. No time accrual, payroll
calendar, eligibility, alternative allowance selection or unit conversion is
inferred. Separate annual and fortnight quotes remain independent prices.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from fractions import Fraction
from hashlib import sha256
from typing import Literal, Self
lazy from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

lazy from src.source_registry import SourceRegistry


class QuoteModel(BaseModel):
    """Strict input with nonblank textual identities and declarations."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    @model_validator(mode="after")
    def nonblank(self) -> Self:
        """Whitespace cannot stand in for identity, provenance or units."""
        if any(isinstance(v, str) and not v.strip() for v in self.__dict__.values()):
            msg = "Quote fields must not be blank"
            raise ValueError(msg)
        return self


class UnitQuote(QuoteModel):
    """One source column's amount per explicitly named unit, without conversion."""

    quote_id: str
    component: str
    unit: str
    amount: Decimal = Field(ge=0, allow_inf_nan=False)
    starts_on: date
    ends_on: date
    known_from: date
    source_id: str
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation: str
    status: Literal["candidate", "accepted", "rejected"]

    @model_validator(mode="after")
    def nonempty_period(self) -> Self:
        """Effective dates are bounded and half open."""
        if self.ends_on <= self.starts_on:
            msg = "Quote date interval must be nonempty"
            raise ValueError(msg)
        return self


class UnitQuoteRelease(QuoteModel):
    """Accepted scoped prices, knowledge date and their held source editions."""

    release_id: str
    method_id: Literal["direct_unit_quote_v1"] = "direct_unit_quote_v1"
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    as_known_on: date
    jurisdiction: str
    employer: str
    classification: str
    sources: SourceRegistry
    quotes: tuple[UnitQuote, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def accepted_prices(self) -> Self:
        """Validate the whole price interval, scope, hash and knowledge horizon."""
        if len({q.quote_id for q in self.quotes}) != len(self.quotes):
            msg = "Duplicate quote identity"
            raise ValueError(msg)
        for quote in self.quotes:
            if quote.status != "accepted" or quote.known_from > self.as_known_on:
                msg = "Quote requires accepted status and known source evidence"
                raise ValueError(msg)
            for when in (quote.starts_on, quote.ends_on - timedelta(days=1)):
                source = self.sources.require_applicable(
                    quote.source_id,
                    when,
                    self.jurisdiction,
                    self.employer,
                    self.classification,
                )
                if source.sha256 != quote.source_sha256:
                    msg = "Quote source hash differs from the held edition"
                    raise ValueError(msg)
                if (
                    source.retrieved_at is None
                    or source.retrieved_at.date() > self.as_known_on
                ):
                    msg = "Source retrieval is after the release knowledge date"
                    raise ValueError(msg)
            for other in self.quotes:
                if (
                    quote.quote_id != other.quote_id
                    and quote.component == other.component
                    and quote.unit == other.unit
                    and quote.starts_on < other.ends_on
                    and other.starts_on < quote.ends_on
                ):
                    msg = "Overlapping quotes for the same component and unit"
                    raise ValueError(msg)
        return self


class QuoteQuantity(QuoteModel):
    """An explicit quantity at a valuation date, not an inferred earned period."""

    quantity_id: str
    quote_id: str
    unit: str
    quantity: Decimal = Field(ge=0, allow_inf_nan=False)
    valued_on: date
    quantity_kind: Literal["observed_use", "analyst_assumption"]
    basis: str


@dataclass(frozen=True)
class UnitQuoteCost:
    """Selected source price, original quantity and exact unrounded cost."""

    quote: UnitQuote
    quantity: QuoteQuantity
    cost: Fraction


@dataclass(frozen=True)
class UnitQuoteResult:
    """Versioned exact result; no automatic joining to an hourly or cash ledger."""

    release_id: str
    release_sha256: str
    method_id: str
    currency: str
    as_known_on: date
    rows: tuple[UnitQuoteCost, ...]
    total: Fraction


def price_units(
    release: UnitQuoteRelease,
    quantities: tuple[QuoteQuantity, ...],
) -> UnitQuoteResult:
    """Price each dated quantity with its exact named quote and denominator unit.

    Equal valuation dates form a static snapshot; distinct dates form an explicit
    event series. A quantity spanning a price change must first be allocated by a
    separately reviewed method. A fraction is caller-supplied, never calculated
    from elapsed days or a guessed number of pay periods. Callers resolve worker
    eligibility, alternative allowances, inclusions, duplicate economic costs
    across ledgers and payment/accrual rules before supplying these quantities.
    """
    release = UnitQuoteRelease.model_validate(release.model_dump())
    quantities = tuple(QuoteQuantity.model_validate(q.model_dump()) for q in quantities)
    if len({q.quantity_id for q in quantities}) != len(quantities):
        msg = "Duplicate quantity identity"
        raise ValueError(msg)
    by_id = {quote.quote_id: quote for quote in release.quotes}
    rows: list[UnitQuoteCost] = []
    for quantity in quantities:
        quote = by_id.get(quantity.quote_id)
        if quote is None:
            msg = "No quote with the requested identity"
            raise ValueError(msg)
        if quote.unit != quantity.unit:
            msg = "Quantity unit does not match the quoted denominator"
            raise ValueError(msg)
        if not quote.starts_on <= quantity.valued_on < quote.ends_on:
            msg = "Quantity valuation date is outside the selected quote"
            raise ValueError(msg)
        rows.append(
            UnitQuoteCost(
                quote,
                quantity,
                Fraction(quote.amount) * Fraction(quantity.quantity),
            ),
        )
    return UnitQuoteResult(
        release.release_id,
        sha256(release.model_dump_json().encode()).hexdigest(),
        release.method_id,
        release.currency,
        release.as_known_on,
        tuple(rows),
        sum((row.cost for row in rows), Fraction(0)),
    )
