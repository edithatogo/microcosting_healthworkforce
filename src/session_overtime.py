# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Explicit work-session thresholds on selected effective-dated price components."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from fractions import Fraction
from typing import Self
from zoneinfo import ZoneInfo

from pydantic import Field, model_validator

from src.costing import Activity, CostRelease, CostResult, RatePeriod, cost_dynamic
from src.roster_costing import OvertimeRule, PayPeriod


def _hours(duration: timedelta) -> Fraction:
    return Fraction(
        (duration.days * 86400 + duration.seconds) * 1000000 + duration.microseconds,
        3600000000,
    )


class WorkSession(PayPeriod):
    """Caller-defined session bounds and complete actual-work history for one worker."""

    session_id: str = Field(min_length=1)
    resource_id: str = Field(min_length=1)
    allocation_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def valid_session(self) -> Self:
        """Reject blank identities and physically impossible individual history."""
        if any(
            not value.strip()
            for value in (self.session_id, self.resource_id, self.allocation_id)
        ):
            msg = "Session identities must be nonblank"
            raise ValueError(msg)
        available = _hours(
            self.history_through.astimezone(UTC) - self.starts_at.astimezone(UTC),
        )
        if Fraction(self.prior_hours) > available:
            msg = "Session history exceeds elapsed time before the history boundary"
            raise ValueError(msg)
        return self


class SessionOvertimeRule(OvertimeRule):
    """Explicit source-reviewed total multiplier on named price components."""

    premium_components: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_components(self) -> Self:
        """Do not infer the loaded basis or count a named component twice."""
        if len(set(self.premium_components)) != len(self.premium_components) or any(
            not key.strip() for key in self.premium_components
        ):
            msg = "Premium component names must be unique and nonblank"
            raise ValueError(msg)
        return self


@dataclass(frozen=True)
class SessionPremium:
    """Exact work quantities and additive premium for one base-rate segment."""

    activity_id: str
    rate_id: str
    starts_at: datetime
    ends_at: datetime
    ordinary_hours: Fraction
    overtime_hours: Fraction
    increment: Fraction


@dataclass(frozen=True)
class SessionOvertimeCost:
    """Retain session, reviewed rule, original base ledger and exact premiums."""

    method_id: str
    session: WorkSession
    rule: SessionOvertimeRule
    base: CostResult
    rows: tuple[SessionPremium, ...]
    total: Fraction
    cumulative_hours: Fraction


def _work(
    session: WorkSession,
    activities: tuple[Activity, ...],
) -> tuple[Activity, ...]:
    ordered = tuple(sorted(activities, key=lambda a: a.starts_at.astimezone(UTC)))
    for item in ordered:
        if (
            item.resource_id != session.resource_id
            or item.allocation_id != session.allocation_id
            or item.resources != 1
        ):
            msg = "Session work requires its one resource and allocation"
            raise ValueError(msg)
        if item.starts_at.astimezone(UTC) < session.history_through.astimezone(
            UTC,
        ) or item.ends_at.astimezone(UTC) > session.ends_at.astimezone(UTC):
            msg = "Work must follow supplied history and remain inside the session"
            raise ValueError(msg)
    if ordered and (
        ordered[0].starts_at.astimezone(UTC) != session.history_through.astimezone(UTC)
    ):
        msg = "Session history must extend to the first supplied work interval"
        raise ValueError(msg)
    return ordered


def _qualify(
    release: CostRelease,
    rule: SessionOvertimeRule,
    rate: RatePeriod,
    bounds: tuple[datetime, datetime],
    timezone: ZoneInfo,
) -> None:
    if not all(key in rate.components for key in rule.premium_components):
        msg = "Selected premium component is absent from a rate"
        raise ValueError(msg)
    for instant in bounds:
        day = instant.astimezone(timezone).date()
        if not rule.effective_from <= day < rule.effective_to:
            msg = "Session overtime rule must cover the entire work interval"
            raise ValueError(msg)
        source = release.sources.require_applicable(
            rule.source_id,
            day,
            rate.jurisdiction,
            rate.employer,
            rate.classification,
        )
        if source.sha256 != rule.source_sha256:
            msg = "Session overtime source hash mismatch"
            raise ValueError(msg)


def cost_session_overtime(
    release: CostRelease,
    session: WorkSession,
    rule: SessionOvertimeRule,
    activities: tuple[Activity, ...],
    local_timezone: str,
) -> SessionOvertimeCost:
    """Add a selected-component premium above an explicit actual-work threshold.

    Session assignment, complete history, eligible work and component selection
    are caller assertions. Gaps and midnight do not reset this supplied session;
    guarantee time and payroll payment timing are not inferred.
    """
    release = CostRelease.model_validate(release.model_dump())
    session = WorkSession.model_validate(session.model_dump())
    rule = SessionOvertimeRule.model_validate(rule.model_dump())
    timezone = ZoneInfo(local_timezone)
    base = cost_dynamic(release, _work(session, activities))
    rates = {rate.rate_id: rate for rate in release.rates}
    cumulative = Fraction(session.prior_hours)
    threshold = Fraction(rule.threshold_hours)
    rows: list[SessionPremium] = []
    for row in base.rows:
        if row.ends_at is None:
            msg = "Session work requires an interval ledger"
            raise ValueError(msg)
        rate = rates[row.rate_id]
        _qualify(
            release,
            rule,
            rate,
            (row.starts_at, row.ends_at - timedelta(microseconds=1)),
            timezone,
        )
        hours = _hours(row.ends_at - row.starts_at)
        overtime = max(Fraction(0), cumulative + hours - threshold) - max(
            Fraction(0),
            cumulative - threshold,
        )
        basis = sum(
            (Fraction(rate.components[key]) for key in rule.premium_components),
            Fraction(0),
        )
        increment = overtime * basis * (Fraction(rule.multiplier) - 1)
        rows.append(
            SessionPremium(
                row.activity_id,
                row.rate_id,
                row.starts_at,
                row.ends_at,
                hours - overtime,
                overtime,
                increment,
            ),
        )
        cumulative += hours
    exact_base = Fraction(base.exact_total_numerator, base.exact_total_denominator)
    return SessionOvertimeCost(
        "session_selected_component_overtime_v1",
        session,
        rule,
        base,
        tuple(rows),
        exact_base + sum((row.increment for row in rows), Fraction(0)),
        cumulative,
    )
