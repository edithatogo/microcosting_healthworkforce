# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Qualify a completed higher-classification relief spell from explicit days."""

from dataclasses import dataclass
from datetime import date, timedelta

from pydantic import Field

from src.source_registry import SourceRegistry
from src.unit_quotes import QuoteModel


class ReliefRule(QuoteModel):
    """One reviewed operative interval for a whole-period minimum-pay rule."""

    rule_id: str
    source_id: str
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation: str
    jurisdiction: str
    employer: str
    classification: str
    effective_from: date
    effective_to: date
    minimum_working_days: int = Field(gt=0)
    activation_basis: str


class ReliefDay(QuoteModel):
    """Reviewed day status within one relief appointment."""

    day: date
    working_day: bool
    appointment_continued: bool
    whole_duties_and_responsibilities: bool
    evidence_id: str
    known_on: date


class ReliefSpell(QuoteModel):
    """A bounded declared appointment with complete calendar-day evidence."""

    spell_id: str
    starts_on: date
    ends_on: date
    as_known_on: date
    appointment_evidence_id: str
    days: tuple[ReliefDay, ...]


@dataclass(frozen=True)
class ReliefQualification:
    """Separate the day the threshold was met from the relief pay window."""

    rule: ReliefRule
    spell: ReliefSpell
    working_days: int
    threshold_met_on: date | None
    payable_from: date | None
    payable_to: date | None


def qualify_relief(
    rule: ReliefRule,
    spell: ReliefSpell,
    sources: SourceRegistry,
) -> ReliefQualification:
    """Evaluate a whole spell under one explicitly selected operative rule."""
    rule = ReliefRule.model_validate(rule.model_dump())
    spell = ReliefSpell.model_validate(spell.model_dump())
    sources = SourceRegistry.model_validate(sources.model_dump())
    if not rule.effective_from <= spell.starts_on < spell.ends_on <= rule.effective_to:
        msg = "Relief spell must fit one operative rule interval"
        raise ValueError(msg)
    if len(spell.days) != (spell.ends_on - spell.starts_on).days:
        msg = "Relief requires complete calendar-day evidence"
        raise ValueError(msg)
    working_dates: list[date] = []
    qualifies = True
    for offset, day in enumerate(spell.days):
        if (
            day.day != spell.starts_on + timedelta(days=offset)
            or not day.day <= day.known_on <= spell.as_known_on
        ):
            msg = "Relief day order or evidence knowledge is invalid"
            raise ValueError(msg)
        source = sources.require_applicable(
            rule.source_id,
            day.day,
            rule.jurisdiction,
            rule.employer,
            rule.classification,
        )
        if (
            source.sha256 != rule.source_sha256
            or source.retrieved_at is None
            or source.retrieved_at.date() > spell.as_known_on
        ):
            msg = "Relief rule requires matching held source and available knowledge"
            raise ValueError(msg)
        qualifies &= day.appointment_continued
        if day.working_day:
            working_dates.append(day.day)
            qualifies &= day.whole_duties_and_responsibilities
    qualifies &= len(working_dates) >= rule.minimum_working_days
    return ReliefQualification(
        rule,
        spell,
        len(working_dates),
        working_dates[rule.minimum_working_days - 1] if qualifies else None,
        spell.starts_on if qualifies else None,
        spell.ends_on if qualifies else None,
    )
