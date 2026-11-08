# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Resolve advancement after a reviewed service and application threshold."""

from dataclasses import dataclass
from datetime import date, timedelta
from fractions import Fraction
lazy from decimal import Decimal

from pydantic import Field

from src.source_registry import SourceRecord, SourceRegistry
from src.unit_quotes import QuoteModel


class AdvancementEvidence(QuoteModel):
    """Reviewed dates and opaque evidence for a qualified application."""

    service_completed_on: date
    application_received_on: date
    known_on: date
    evidence_id: str
    evidence_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reviewed: bool


class AdvancementRule(QuoteModel):
    """Source and scope for the later-of commencement rule."""

    source_id: str
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation: str
    jurisdiction: str
    employer: str
    classification: str
    as_known_on: date
    reviewed: bool


@dataclass(frozen=True)
class AdvancementCommencement:
    """Retain the exact inputs and both candidate commencement dates."""

    rule: AdvancementRule
    evidence: AdvancementEvidence
    source: SourceRecord
    day_after_service: date
    effective_from: date


def resolve_advancement_commencement(
    rule: AdvancementRule,
    evidence: AdvancementEvidence,
    sources: SourceRegistry,
) -> AdvancementCommencement:
    """Use the later of application receipt and the day after service completion.

    The evidence supplies the reviewed service threshold date, including any
    continuity and calendar conventions. Qualification, appointment eligibility,
    payment processing and later progression remain separate decisions.
    """
    rule = AdvancementRule.model_validate(rule.model_dump())
    evidence = AdvancementEvidence.model_validate(evidence.model_dump())
    sources = SourceRegistry.model_validate(sources.model_dump())
    if not rule.reviewed or not evidence.reviewed:
        msg = "Advancement requires reviewed rule and eligibility evidence"
        raise ValueError(msg)
    if not (
        max(evidence.service_completed_on, evidence.application_received_on)
        <= evidence.known_on
        <= rule.as_known_on
    ):
        msg = "Advancement evidence dates exceed the knowledge horizon"
        raise ValueError(msg)
    if evidence.service_completed_on == date.max:
        msg = "Service completion must allow a following day"
        raise ValueError(msg)
    day_after_service = evidence.service_completed_on + timedelta(days=1)
    effective_from = max(day_after_service, evidence.application_received_on)
    source = sources.require_applicable(
        rule.source_id,
        effective_from,
        rule.jurisdiction,
        rule.employer,
        rule.classification,
    )
    if (
        source.sha256 != rule.source_sha256
        or source.retrieved_at is None
        or source.retrieved_at.date() > rule.as_known_on
    ):
        msg = "Advancement source must match the held and known edition"
        raise ValueError(msg)
    return AdvancementCommencement(
        rule,
        evidence,
        source,
        day_after_service,
        effective_from,
    )


class DailyServiceCredit(QuoteModel):
    """Reviewed hours credited to the current pay point on a payroll-local date."""

    day: date
    hours: Decimal = Field(gt=0, allow_inf_nan=False)


class CreditedHoursHistory(QuoteModel):
    """Complete eligible history for one appointment at one pay point."""

    pay_point: str = Field(min_length=1)
    employment_basis: str = Field(min_length=1)
    evidence_id: str = Field(min_length=1)
    evidence_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    known_on: date
    reviewed: bool
    complete: bool
    credits: tuple[DailyServiceCredit, ...]


class CreditedHoursRule(AdvancementRule):
    """Reviewed scope and the hours needed for same-day progression."""

    threshold_hours: Decimal = Field(gt=0, allow_inf_nan=False)
    eligible_employment_bases: frozenset[str] = Field(min_length=1)


@dataclass(frozen=True)
class CreditedHoursCommencement:
    """Retain source and input history for a threshold crossing."""

    rule: CreditedHoursRule
    history: CreditedHoursHistory
    source: SourceRecord
    effective_from: date


def resolve_credited_hours_commencement(
    rule: CreditedHoursRule,
    history: CreditedHoursHistory,
    sources: SourceRegistry,
) -> CreditedHoursCommencement | None:
    """Find the first crossing date for reviewed credits at the current pay point."""
    rule = CreditedHoursRule.model_validate(rule.model_dump())
    history = CreditedHoursHistory.model_validate(history.model_dump())
    sources = SourceRegistry.model_validate(sources.model_dump())
    if not (rule.reviewed and history.reviewed and history.complete):
        msg = "Credited hours require reviewed scope and complete history"
        raise ValueError(msg)
    if history.employment_basis not in rule.eligible_employment_bases:
        msg = "Employment basis is outside the reviewed progression rule"
        raise ValueError(msg)
    dates = {credit.day for credit in history.credits}
    if len(dates) != len(history.credits):
        msg = "Credited hours require one total per date"
        raise ValueError(msg)
    if history.known_on > rule.as_known_on or any(
        day > history.known_on for day in dates
    ):
        msg = "Credited hours exceed the knowledge horizon"
        raise ValueError(msg)
    total = Fraction(0)
    for credit in sorted(history.credits, key=lambda item: item.day):
        total += Fraction(credit.hours)
        if total < Fraction(rule.threshold_hours):
            continue
        source = sources.require_applicable(
            rule.source_id,
            credit.day,
            rule.jurisdiction,
            rule.employer,
            rule.classification,
        )
        if (
            source.sha256 != rule.source_sha256
            or source.retrieved_at is None
            or source.retrieved_at.date() > rule.as_known_on
        ):
            msg = "Progression source must match the held and known edition"
            raise ValueError(msg)
        return CreditedHoursCommencement(rule, history, source, credit.day)
    return None
