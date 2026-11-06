# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Resolve explicitly supplied first-full-pay-period commencement boundaries."""

from datetime import UTC, date, datetime
from typing import Self
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.source_registry import SourceRegistry


class PeriodCalendar(BaseModel):
    """Supplied contiguous payroll boundaries; period length is never guessed."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    calendar_id: str = Field(min_length=1)
    boundaries: tuple[datetime, ...] = Field(min_length=2)
    complete: bool

    @field_validator("boundaries")
    @classmethod
    def aware_boundaries(cls, values: tuple[datetime, ...]) -> tuple[datetime, ...]:
        """Normalize all supplied instants before ordering and comparison."""
        if any(value.utcoffset() is None for value in values):
            msg = "Pay-period boundaries must be timezone-aware"
            raise ValueError(msg)
        return tuple(value.astimezone(UTC) for value in values)

    @model_validator(mode="after")
    def complete_ordered(self) -> Self:
        """Require a complete boundary assertion and strictly increasing instants."""
        if not self.complete or any(
            a >= b for a, b in zip(self.boundaries, self.boundaries[1:], strict=False)
        ):
            msg = "Pay-period boundaries must be complete and strictly increasing"
            raise ValueError(msg)
        return self


class RetrospectiveAuthority(BaseModel):
    """Reviewed, explicit entitlement interval and its known-at boundary."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    entitlement_from: date
    entitlement_to: date
    known_from: date
    as_known_at: date
    citation: str = Field(min_length=1)
    reviewed: bool

    @model_validator(mode="after")
    def valid_authority(self) -> Self:
        """Reject unreviewed, unbounded or not-yet-known authority."""
        if (
            not self.reviewed
            or not self.citation.strip()
            or self.entitlement_to <= self.entitlement_from
            or self.as_known_at < self.known_from
        ):
            msg = (
                "Retrospective authority requires review, dates and available knowledge"
            )
            raise ValueError(msg)
        return self


class FirstFullPeriodRule(BaseModel):
    """A reviewed rule for a specific scope and explicit trigger instant."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    rule_id: str = Field(min_length=1)
    jurisdiction: str = Field(min_length=1)
    employer: str = Field(min_length=1)
    classification: str = Field(min_length=1)
    timezone: str = Field(min_length=1)
    trigger_at: datetime
    source_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation: str = Field(min_length=1)
    reviewed: bool
    retrospective: RetrospectiveAuthority | None = None

    @model_validator(mode="after")
    def valid_rule(self) -> Self:
        """Require a reviewed source and an unambiguous trigger instant."""
        ZoneInfo(self.timezone)
        if (
            not self.reviewed
            or not self.citation.strip()
            or self.trigger_at.utcoffset() is None
        ):
            msg = "Pay-period rule requires review, citation and an aware trigger"
            raise ValueError(msg)
        return self


class ResolvedPeriod(BaseModel):
    """A half-open period and all evidence needed to reproduce the selection."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    rule: FirstFullPeriodRule
    calendar: PeriodCalendar
    starts_at: datetime
    ends_at: datetime


def first_full_period(
    rule: FirstFullPeriodRule,
    calendar: PeriodCalendar,
    sources: SourceRegistry,
) -> ResolvedPeriod:
    """Select the first complete period starting at or after the trigger.

    The caller supplies the correct trigger instant, a complete payroll calendar,
    an applicable reviewed source and the rule's eligibility. This method does
    not infer work performed, wage rates, award precedence, backpay or cash timing.
    """
    rule = FirstFullPeriodRule.model_validate(rule.model_dump())
    calendar = PeriodCalendar.model_validate(calendar.model_dump())
    sources = SourceRegistry.model_validate(sources.model_dump())
    trigger = rule.trigger_at.astimezone(UTC)
    if calendar.boundaries[0] > trigger:
        msg = "Calendar must include a boundary at or before the trigger"
        raise ValueError(msg)
    candidate = next(
        (
            index
            for index, start in enumerate(calendar.boundaries[:-1])
            if start >= trigger
        ),
        None,
    )
    if candidate is None:
        msg = "Calendar does not include the next complete pay period"
        raise ValueError(msg)
    start, end = calendar.boundaries[candidate : candidate + 2]
    zone = ZoneInfo(rule.timezone)
    evidence = rule.retrospective
    if evidence is not None:
        for known_date in (evidence.known_from, evidence.as_known_at):
            source = sources.require_applicable(
                rule.source_id,
                known_date,
                rule.jurisdiction,
                rule.employer,
                rule.classification,
            )
            if source.sha256 != rule.source_sha256:
                msg = "Pay-period rule source hash mismatch"
                raise ValueError(msg)
    for day in (trigger.astimezone(zone).date(), start.astimezone(zone).date()):
        if evidence is not None and day < evidence.known_from:
            if not evidence.entitlement_from <= day < evidence.entitlement_to:
                msg = "Date outside reviewed retrospective entitlement interval"
                raise ValueError(msg)
        else:
            source = sources.require_applicable(
                rule.source_id,
                day,
                rule.jurisdiction,
                rule.employer,
                rule.classification,
            )
            if source.sha256 != rule.source_sha256:
                msg = "Pay-period rule source hash mismatch"
                raise ValueError(msg)
    return ResolvedPeriod(rule=rule, calendar=calendar, starts_at=start, ends_at=end)
