# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Price one explicit alternative per non-overlapping resource exposure window."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from itertools import pairwise
from typing import Literal, Self
from zoneinfo import ZoneInfo

from pydantic import Field, field_validator, model_validator

from src.unit_quotes import (
    NonnegativeQuantity,
    QuoteModel,
    QuoteQuantity,
    UnitQuoteRelease,
    UnitQuoteResult,
    price_units,
)


class ExclusiveQuoteRule(QuoteModel):
    """One source-qualified alternative group, never an automatic highest choice."""

    rule_id: str
    components: tuple[str, ...] = Field(min_length=2)
    unit: str
    local_timezone: str
    source_id: str
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation: str
    reviewed: bool
    interpretation_kind: Literal["source_reviewed", "analyst_assumption"]
    interpretation_basis: str
    effective_from: date
    effective_to: date
    as_known_on: date
    jurisdiction: str
    employer: str
    classification: str

    @model_validator(mode="after")
    def valid_policy(self) -> Self:
        """Require distinct alternatives, review and a nonempty operative period."""
        ZoneInfo(self.local_timezone)
        if (
            not self.reviewed
            or self.effective_to <= self.effective_from
            or len(set(self.components)) != len(self.components)
            or any(not name.strip() for name in self.components)
        ):
            msg = (
                "Exclusive policy needs review, dates and distinct nonblank components"
            )
            raise ValueError(msg)
        return self


class QuoteExposureWindow(QuoteModel):
    """An upstream-reviewed eligible window and explicit quantity."""

    allocation_id: str
    resource_id: str
    starts_at: datetime
    ends_at: datetime
    valued_on: date
    quantity: NonnegativeQuantity
    eligibility_verified: bool
    history_complete: bool
    selection_basis: str
    input_kind: Literal["observed_case_evidence", "analyst_assumption"]
    evidence_id: str
    evidence_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    known_on: date

    @field_validator("starts_at", "ends_at")
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        """Compare absolute instants while leaving local units to the caller."""
        if value.utcoffset() is None:
            msg = "Allocation times must be timezone aware"
            raise ValueError(msg)
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def complete_window(self) -> Self:
        """Unknown eligibility/history cannot become a passing zero quantity."""
        if (
            self.ends_at <= self.starts_at
            or not self.eligibility_verified
            or not self.history_complete
        ):
            msg = (
                "Allocation requires a positive window "
                "and qualified eligibility/history"
            )
            raise ValueError(msg)
        return self


class ExclusiveQuoteAllocation(QuoteExposureWindow):
    """One chosen alternative for an upstream-qualified exposure window."""

    quote_id: str


@dataclass(frozen=True)
class ExclusiveQuoteResult:
    """Retain reviewed policy, selected windows and exact shared price ledger."""

    rule: ExclusiveQuoteRule
    allocations: tuple[ExclusiveQuoteAllocation, ...]
    scenario: bool
    prices: UnitQuoteResult


def validate_quote_exposures(
    rule: ExclusiveQuoteRule,
    release: UnitQuoteRelease,
    exposures: tuple[QuoteExposureWindow, ...],
) -> None:
    """Validate complete source-qualified windows independently of price selection."""
    rule = ExclusiveQuoteRule.model_validate(dict(rule))
    release = UnitQuoteRelease.model_validate(release.model_dump())
    exposures = tuple(QuoteExposureWindow.model_validate(dict(a)) for a in exposures)
    if (rule.jurisdiction, rule.employer, rule.classification) != (
        release.jurisdiction,
        release.employer,
        release.classification,
    ) or rule.as_known_on != release.as_known_on:
        msg = "Exclusive policy and prices require matching scope and knowledge date"
        raise ValueError(msg)
    if not exposures or len({a.allocation_id for a in exposures}) != len(exposures):
        msg = "Supply a nonempty allocation set with unique identities"
        raise ValueError(msg)
    ordered = sorted(exposures, key=lambda a: (a.resource_id, a.starts_at))
    if any(
        a.resource_id == b.resource_id and b.starts_at < a.ends_at
        for a, b in pairwise(ordered)
    ):
        msg = "Alternative allocation windows overlap for the same resource"
        raise ValueError(msg)
    zone = ZoneInfo(rule.local_timezone)
    for allocation in ordered:
        first = allocation.starts_at.astimezone(zone).date()
        last = (allocation.ends_at - timedelta(microseconds=1)).astimezone(zone).date()
        if (
            not rule.effective_from <= first <= allocation.valued_on <= last
            or last >= rule.effective_to
            or allocation.known_on > rule.as_known_on
            or (
                allocation.input_kind == "observed_case_evidence"
                and last > allocation.known_on
            )
        ):
            msg = "Allocation dates or case evidence exceed policy/knowledge coverage"
            raise ValueError(msg)
        for day in (first, last):
            source = release.sources.require_applicable(
                rule.source_id,
                day,
                rule.jurisdiction,
                rule.employer,
                rule.classification,
            )
            if (
                source.sha256 != rule.source_sha256
                or source.retrieved_at is None
                or source.retrieved_at.date() > rule.as_known_on
            ):
                msg = "Exclusive policy requires matching held hash and known source"
                raise ValueError(msg)


def price_exclusive_quotes(
    rule: ExclusiveQuoteRule,
    release: UnitQuoteRelease,
    allocations: tuple[ExclusiveQuoteAllocation, ...],
) -> ExclusiveQuoteResult:
    """Prevent overlapping alternatives within one complete supplied allocation set.

    No geography, proration, maximum choice, rolling cap or cross-call duplication
    is inferred. Price/policy changes require explicit non-overlapping splits.
    """
    rule = ExclusiveQuoteRule.model_validate(dict(rule))
    release = UnitQuoteRelease.model_validate(release.model_dump())
    allocations = tuple(
        ExclusiveQuoteAllocation.model_validate(dict(a)) for a in allocations
    )
    exposures = tuple(
        QuoteExposureWindow.model_validate(
            {k: v for k, v in dict(a).items() if k != "quote_id"},
        )
        for a in allocations
    )
    validate_quote_exposures(rule, release, exposures)
    ordered = tuple(
        sorted(
            allocations,
            key=lambda a: (a.resource_id, a.starts_at, a.allocation_id),
        ),
    )
    zone = ZoneInfo(rule.local_timezone)
    quotes = {q.quote_id: q for q in release.quotes}
    quantities: list[QuoteQuantity] = []
    for allocation in ordered:
        first = allocation.starts_at.astimezone(zone).date()
        last = (allocation.ends_at - timedelta(microseconds=1)).astimezone(zone).date()
        quote = quotes.get(allocation.quote_id)
        if (
            quote is None
            or quote.component not in rule.components
            or quote.unit != rule.unit
            or not quote.starts_on <= first <= last < quote.ends_on
        ):
            msg = (
                "Selected alternative must match group/unit and cover the whole window"
            )
            raise ValueError(msg)
        quantities.append(
            QuoteQuantity(
                quantity_id=allocation.allocation_id,
                quote_id=allocation.quote_id,
                unit=rule.unit,
                quantity=allocation.quantity,
                valued_on=allocation.valued_on,
                quantity_kind=(
                    "observed_use"
                    if allocation.input_kind == "observed_case_evidence"
                    else "analyst_assumption"
                ),
                basis=allocation.selection_basis,
            ),
        )
    return ExclusiveQuoteResult(
        rule,
        ordered,
        rule.interpretation_kind == "analyst_assumption"
        or any(a.input_kind == "analyst_assumption" for a in ordered),
        price_units(release, tuple(quantities)),
    )
