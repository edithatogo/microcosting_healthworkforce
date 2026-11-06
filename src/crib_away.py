# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Price complete source-qualified crib occasions without inferring entitlement."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from itertools import pairwise
from typing import Literal, Self
from zoneinfo import ZoneInfo
lazy from datetime import date

from pydantic import Field, field_validator, model_validator

from src.unit_quotes import QuoteModel, QuoteQuantity, UnitQuoteRelease, price_units
lazy from src.unit_quotes import UnitQuoteResult

type InputKind = Literal["source_reviewed", "analyst_assumption"]
type CaseEvidenceKind = Literal["observed_case_evidence", "analyst_assumption"]


def _utc(value: datetime) -> datetime:
    if value.utcoffset() is None:
        msg = "Crib shift and occasion times must be timezone aware"
        raise ValueError(msg)
    return value.astimezone(UTC)


class CribAwayRule(QuoteModel):
    """Reviewed monetary policy and distinct one/two-entitlement quote components."""

    rule_id: str
    one_crib_component: str
    two_crib_component: str
    unit: str
    local_timezone: str
    interpretation_kind: InputKind
    interpretation_basis: str
    source_id: str
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation: str
    reviewed: bool
    effective_from: date
    effective_to: date
    as_known_on: date
    jurisdiction: str
    employer: str
    classification: str

    @model_validator(mode="after")
    def reviewed_scope(self) -> Self:
        """Require reviewed coverage and distinct alternative contexts."""
        ZoneInfo(self.local_timezone)
        if (
            not self.reviewed
            or self.effective_to <= self.effective_from
            or self.one_crib_component == self.two_crib_component
        ):
            msg = (
                "Crib rule needs reviewed coverage and distinct alternative components"
            )
            raise ValueError(msg)
        return self


class CribShift(QuoteModel):
    """One complete case with explicitly qualified eligibility and entitlement."""

    shift_id: str
    resource_id: str
    starts_at: datetime
    ends_at: datetime
    entitled_cribs: int = Field(ge=1, le=2)
    eligibility_verified: bool
    eligibility_basis: str
    entitlement_verified: bool
    entitlement_basis: str
    history_complete: bool
    input_kind: CaseEvidenceKind
    evidence_id: str
    evidence_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    known_on: date

    @field_validator("starts_at", "ends_at")
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        """Order absolute instants without equating roster hours with elapsed time."""
        return _utc(value)

    @model_validator(mode="after")
    def complete_case(self) -> Self:
        """Unknown eligibility/entitlement/history cannot produce a passing zero."""
        if (
            self.ends_at <= self.starts_at
            or not self.eligibility_verified
            or not self.entitlement_verified
            or not self.history_complete
        ):
            msg = "Require positive shift, verified eligibility/entitlement and history"
            raise ValueError(msg)
        return self


class CribOccasion(QuoteModel):
    """One entitled slot with an explicit directed-away fact or known false."""

    break_id: str
    shift_id: str
    slot: int = Field(ge=1, le=2)
    occasion_at: datetime
    directed_away: bool
    quote_id: str | None
    input_kind: CaseEvidenceKind
    evidence_id: str
    evidence_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    known_on: date
    basis: str

    @field_validator("occasion_at")
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        """Retain an explicit occasion valuation instant."""
        return _utc(value)

    @model_validator(mode="after")
    def explicit_quote(self) -> Self:
        """Only a directed-away occasion selects a nonblank monetary quote."""
        if self.directed_away != (self.quote_id is not None):
            msg = "Directed occasions require quotes; known non-away slots require null"
            raise ValueError(msg)
        return self


@dataclass(frozen=True)
class CribAwayResult:
    """Complete original case/slot evidence and exact directed-occasion pricing."""

    method_id: str
    rule: CribAwayRule
    rule_sha256: str
    shift: CribShift
    occasions: tuple[CribOccasion, ...]
    directed_away_count: int
    mode: Literal["scenario", "reviewed_case_inputs"]
    pricing: UnitQuoteResult


def _coverage(rule: CribAwayRule, release: UnitQuoteRelease, day: date) -> None:
    if not rule.effective_from <= day < rule.effective_to:
        msg = "Crib policy does not cover the requested date"
        raise ValueError(msg)
    source = release.sources.require_applicable(
        rule.source_id,
        day,
        rule.jurisdiction,
        rule.employer,
        rule.classification,
    )
    if source.sha256 != rule.source_sha256:
        msg = "Crib policy source hash mismatch"
        raise ValueError(msg)
    if source.retrieved_at is None or source.retrieved_at.date() > rule.as_known_on:
        msg = "Crib policy source exceeds the knowledge date"
        raise ValueError(msg)


def _known_evidence(
    rule: CribAwayRule,
    shift: CribShift,
    occasions: tuple[CribOccasion, ...],
    zone: ZoneInfo,
) -> None:
    if max([shift.known_on, *(o.known_on for o in occasions)]) > rule.as_known_on:
        msg = "Crib evidence exceeds the knowledge date"
        raise ValueError(msg)
    last = (shift.ends_at - timedelta(microseconds=1)).astimezone(zone).date()
    if shift.input_kind == "observed_case_evidence" and last > shift.known_on:
        msg = "Observed complete-shift evidence cannot precede the shift"
        raise ValueError(msg)
    for occasion in occasions:
        if (
            occasion.input_kind == "observed_case_evidence"
            and occasion.occasion_at.astimezone(zone).date() > occasion.known_on
        ):
            msg = "Observed occasion evidence cannot precede its occurrence"
            raise ValueError(msg)


def price_crib_away(
    rule: CribAwayRule,
    release: UnitQuoteRelease,
    shift: CribShift,
    occasions: tuple[CribOccasion, ...],
) -> CribAwayResult:
    """Validate all entitled slots and price one unit per directed occasion.

    Eligibility, source-qualified entitlement and break-schedule exceptions are
    upstream case facts or assumptions. The method does not derive entitlement
    from elapsed hours or add paid break time/extra ordinary-time compensation.
    Each supplied occasion's local date selects its explicit price version.
    """
    rule = CribAwayRule.model_validate(dict(rule))
    release = UnitQuoteRelease.model_validate(release.model_dump())
    shift = CribShift.model_validate(dict(shift))
    occasions = tuple(CribOccasion.model_validate(dict(o)) for o in occasions)
    if (release.jurisdiction, release.employer, release.classification) != (
        rule.jurisdiction,
        rule.employer,
        rule.classification,
    ) or release.as_known_on != rule.as_known_on:
        msg = "Crib policy and prices require matching scope and knowledge date"
        raise ValueError(msg)
    zone = ZoneInfo(rule.local_timezone)
    _known_evidence(rule, shift, occasions, zone)
    _coverage(rule, release, shift.starts_at.astimezone(zone).date())
    last = (shift.ends_at - timedelta(microseconds=1)).astimezone(zone).date()
    _coverage(rule, release, last)
    if (
        len(occasions) != shift.entitled_cribs
        or {o.slot for o in occasions} != set(range(1, shift.entitled_cribs + 1))
        or len({o.break_id for o in occasions}) != len(occasions)
    ):
        msg = "Supply exactly one distinct record for every entitled crib slot"
        raise ValueError(msg)
    ordered = tuple(sorted(occasions, key=lambda o: o.slot))
    if any(
        o.shift_id != shift.shift_id
        or not shift.starts_at <= o.occasion_at < shift.ends_at
        for o in ordered
    ) or any(a.occasion_at >= b.occasion_at for a, b in pairwise(ordered)):
        msg = "Crib occasions must belong to the shift and increase in slot order"
        raise ValueError(msg)
    expected = (
        rule.one_crib_component
        if shift.entitled_cribs == 1
        else rule.two_crib_component
    )
    quotes = {q.quote_id: q for q in release.quotes}
    quantities: list[QuoteQuantity] = []
    for occasion in ordered:
        if not occasion.directed_away:
            continue
        quote = quotes.get(occasion.quote_id or "")
        if quote is None or quote.component != expected or quote.unit != rule.unit:
            msg = "Selected quote must match the shift entitlement context and unit"
            raise ValueError(msg)
        quantities.append(
            QuoteQuantity(
                quantity_id=occasion.break_id,
                quote_id=quote.quote_id,
                unit=rule.unit,
                quantity=Decimal(1),
                valued_on=occasion.occasion_at.astimezone(zone).date(),
                quantity_kind=(
                    "observed_use"
                    if occasion.input_kind == "observed_case_evidence"
                    else "analyst_assumption"
                ),
                basis=occasion.basis,
            ),
        )
    pricing = price_units(release, tuple(quantities))
    reviewed = (
        rule.interpretation_kind == "source_reviewed"
        and shift.input_kind == "observed_case_evidence"
        and all(o.input_kind == "observed_case_evidence" for o in ordered)
    )
    return CribAwayResult(
        "explicit_entitlement_directed_crib_occasions_v1",
        rule,
        sha256(rule.model_dump_json().encode()).hexdigest(),
        shift,
        ordered,
        len(quantities),
        "reviewed_case_inputs" if reviewed else "scenario",
        pricing,
    )
