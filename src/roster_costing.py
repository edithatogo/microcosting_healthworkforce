# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Explicit, bounded cumulative overtime calculation for one worker and period."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from fractions import Fraction
from typing import Self
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.conditions import ConditionRelease, cost_condition_activity
from src.costing import Activity
lazy from src.conditions import ConditionCostSegment


class PayPeriod(BaseModel):
    """A supplied period and complete cumulative history to the first activity."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    starts_at: datetime
    ends_at: datetime
    prior_hours: Decimal = Field(ge=0, allow_inf_nan=False)
    history_through: datetime
    history_complete: bool

    @model_validator(mode="after")
    def valid_period(self) -> Self:
        """Require explicit aware instants and an affirmative history assertion."""
        if any(
            x.utcoffset() is None
            for x in (self.starts_at, self.ends_at, self.history_through)
        ):
            msg = "Pay-period and history instants must be timezone-aware"
            raise ValueError(msg)
        if not self.history_complete:
            msg = "Complete prior and in-period history must be explicitly supplied"
            raise ValueError(msg)
        if (
            not self.starts_at.astimezone(UTC)
            <= self.history_through.astimezone(UTC)
            < self.ends_at.astimezone(UTC)
        ):
            msg = "History boundary must be inside pay period"
            raise ValueError(msg)
        if self.prior_hours and (
            self.history_through.astimezone(UTC) == self.starts_at.astimezone(UTC)
        ):
            msg = "Prior hours must be zero at the start of the pay period"
            raise ValueError(msg)
        return self


class OvertimeRule(BaseModel):
    """A reviewed threshold and salary-only multiplier, never inferred from an award."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    rule_id: str = Field(min_length=1)
    threshold_hours: Decimal = Field(ge=0, allow_inf_nan=False)
    multiplier: Decimal = Field(ge=1, allow_inf_nan=False)
    source_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation: str = Field(min_length=1)
    effective_from: date
    effective_to: date
    reviewed: bool

    @model_validator(mode="after")
    def valid_rule(self) -> Self:
        """Require a bounded interval and explicit review declaration."""
        if (
            not self.reviewed
            or not self.citation.strip()
            or self.effective_to <= self.effective_from
        ):
            msg = "Rule requires review, citation and a nonempty effective period"
            raise ValueError(msg)
        return self


class RosterCostRow(BaseModel):
    """Auditable activity segment, ordinary and threshold overtime hours."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    activity_id: str
    starts_at: datetime
    ends_at: datetime
    ordinary_hours: Decimal
    overtime_hours: Decimal
    components: dict[str, Decimal]
    overtime_increment: Decimal
    condition_ids: tuple[str, ...]
    rule_id: str
    source_id: str
    source_sha256: str
    citation: str


class RosterCostResult(BaseModel):
    """Result of one complete asserted period with no hidden pay-period defaults."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    release_id: str
    method_id: str = "cumulative_salary_overtime_v1"
    total: Decimal
    ordinary_hours: Decimal
    overtime_hours: Decimal
    prior_hours: Decimal
    exact_total_numerator: int
    exact_total_denominator: int = Field(gt=0)
    exact_premium_numerator: int
    exact_premium_denominator: int = Field(gt=0)
    rows: tuple[RosterCostRow, ...]


def _require_rule_coverage(
    release: ConditionRelease,
    rule: OvertimeRule,
    day: date,
    final_day: date,
) -> None:
    if day < rule.effective_from or final_day >= rule.effective_to:
        msg = "Overtime rule does not cover activity date"
        raise ValueError(msg)
    for check_day in (day, final_day):
        source = release.sources.require_applicable(
            rule.source_id,
            check_day,
            release.jurisdiction,
            release.employer,
            release.classification,
        )
        if source.sha256 != rule.source_sha256:
            msg = "Overtime rule source hash mismatch"
            raise ValueError(msg)


def _exact_segment(
    release: ConditionRelease,
    rule: OvertimeRule,
    segment: ConditionCostSegment,
    day: date,
    cumulative: Fraction,
) -> tuple[Fraction, Fraction, Fraction]:
    elapsed = segment.ends_at - segment.starts_at
    microseconds = (
        elapsed.days * 86400 + elapsed.seconds
    ) * 1000000 + elapsed.microseconds
    hours = Fraction(microseconds, 3600000000)
    ordinary = min(hours, max(Fraction(0), Fraction(rule.threshold_hours) - cumulative))
    salary = next(
        c
        for c in release.conditions
        if c.kind == "salary" and c.effective_from <= day < c.effective_to
    )
    paid = next(
        c
        for c in release.conditions
        if c.kind == "paid_hours" and c.effective_from <= day < c.effective_to
    )
    premium = (
        Fraction(salary.value)
        / Fraction(paid.value)
        * (Fraction(rule.multiplier) - 1)
        * (hours - ordinary)
    )
    if premium and salary.included_components:
        msg = "Overtime premium requires salary without bundled components"
        raise ValueError(msg)
    return hours, ordinary, premium


def _require_single_worker(ordered: list[Activity]) -> None:
    if (
        len({a.activity_id for a in ordered}) != len(ordered)
        or len({a.resource_id for a in ordered}) != 1
    ):
        msg = "Activities require unique identities and one resource"
        raise ValueError(msg)
    if len({a.allocation_id for a in ordered}) > 1:
        msg = "One overtime period requires one consistent allocation identity"
        raise ValueError(msg)


def cost_overtime_period(
    release: ConditionRelease,
    period: PayPeriod,
    rule: OvertimeRule,
    activities: tuple[Activity, ...],
    local_timezone: str,
) -> RosterCostResult:
    """Cost one worker's complete period; multiply salary only above threshold.

    Other hourly components remain unchanged. The caller must supply all eligible
    hours and an applicable reviewed rule; no eligibility, exclusions, rounding,
    premium stacking or pay-period boundaries are inferred.
    """
    release = ConditionRelease.model_validate(release.model_dump())
    period = PayPeriod.model_validate(period.model_dump())
    rule = OvertimeRule.model_validate(rule.model_dump())
    zone = ZoneInfo(local_timezone)
    ordered = sorted(
        (Activity.model_validate(a.model_dump()) for a in activities),
        key=lambda a: a.starts_at.astimezone(UTC),
    )
    if not ordered:
        msg = "At least one activity and its complete history are required"
        raise ValueError(msg)
    _require_single_worker(ordered)
    if ordered[0].starts_at.astimezone(UTC) != period.history_through.astimezone(UTC):
        msg = "History must be stated through the first activity start"
        raise ValueError(msg)
    previous_end = period.starts_at.astimezone(UTC)
    exact_cumulative = Fraction(period.prior_hours)
    exact_ordinary_total = Fraction(0)
    exact_overtime_total = Fraction(0)
    exact_base = Fraction(0)
    exact_premium = Fraction(0)
    rows: list[RosterCostRow] = []
    for activity in ordered:
        start = activity.starts_at.astimezone(UTC)
        end = activity.ends_at.astimezone(UTC)
        if start < previous_end:
            msg = "Activities overlap within one resource"
            raise ValueError(msg)
        if start < period.starts_at.astimezone(UTC) or end > period.ends_at.astimezone(
            UTC,
        ):
            msg = "Activity falls outside the explicit pay period"
            raise ValueError(msg)
        if activity.resources != Decimal(1):
            msg = "Overtime requires exactly one resource"
            raise ValueError(msg)
        previous_end = end
        activity_result = cost_condition_activity(release, activity, local_timezone)
        exact_base += Fraction(
            activity_result.exact_total_numerator,
            activity_result.exact_total_denominator,
        )
        for segment in activity_result.segments:
            day = segment.starts_at.astimezone(zone).date()
            final_day = (
                (segment.ends_at - timedelta(microseconds=1)).astimezone(zone).date()
            )
            _require_rule_coverage(release, rule, day, final_day)
            exact_hours, exact_ordinary, premium_delta = _exact_segment(
                release,
                rule,
                segment,
                day,
                exact_cumulative,
            )
            exact_overtime = exact_hours - exact_ordinary
            ordinary = Decimal(exact_ordinary.numerator) / exact_ordinary.denominator
            overtime = Decimal(exact_overtime.numerator) / exact_overtime.denominator
            increment = Decimal(premium_delta.numerator) / premium_delta.denominator
            exact_cumulative += exact_hours
            exact_ordinary_total += exact_ordinary
            exact_overtime_total += exact_overtime
            exact_premium += premium_delta
            rows.append(
                RosterCostRow(
                    activity_id=activity.activity_id,
                    starts_at=segment.starts_at,
                    ends_at=segment.ends_at,
                    ordinary_hours=ordinary,
                    overtime_hours=overtime,
                    components=segment.components,
                    overtime_increment=increment,
                    condition_ids=segment.condition_ids,
                    rule_id=rule.rule_id,
                    source_id=rule.source_id,
                    source_sha256=rule.source_sha256,
                    citation=rule.citation,
                ),
            )
    exact_total = exact_base + exact_premium
    return RosterCostResult(
        release_id=release.release_id,
        total=Decimal(exact_total.numerator) / exact_total.denominator,
        ordinary_hours=(
            Decimal(exact_ordinary_total.numerator) / exact_ordinary_total.denominator
        ),
        overtime_hours=(
            Decimal(exact_overtime_total.numerator) / exact_overtime_total.denominator
        ),
        prior_hours=period.prior_hours,
        exact_total_numerator=exact_total.numerator,
        exact_total_denominator=exact_total.denominator,
        exact_premium_numerator=exact_premium.numerator,
        exact_premium_denominator=exact_premium.denominator,
        rows=tuple(rows),
    )
