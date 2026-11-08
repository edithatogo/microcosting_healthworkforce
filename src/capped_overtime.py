# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Explicit daily capped-salary overtime adjustment to an existing base ledger."""

from dataclasses import dataclass
from datetime import UTC, date, timedelta
from decimal import Decimal
from fractions import Fraction
from typing import Self
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.conditions import (
    ConditionCostResult,
    ConditionRelease,
    cost_condition_activity,
)
from src.costing import Activity


class DailyTier(BaseModel):
    """Starting cumulative overtime hours and the total salary multiplier."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    starts_at_hours: Decimal = Field(ge=0, allow_inf_nan=False)
    multiplier: Decimal = Field(gt=0, allow_inf_nan=False)


class CappedDailyRule(BaseModel):
    """A specifically reviewed cash rule and hourly salary cap, with provenance."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    rule_id: str = Field(min_length=1)
    salary_cap_hourly: Decimal = Field(ge=0, allow_inf_nan=False)
    tiers: tuple[DailyTier, ...] = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation: str = Field(min_length=1)
    effective_from: date
    effective_to: date
    reviewed: bool
    time_off_cash_multiplier: Decimal | None = Field(
        default=None,
        ge=0,
        allow_inf_nan=False,
    )

    @model_validator(mode="after")
    def validate_rule(self) -> Self:
        """Require a sourced contiguous schedule starting at zero."""
        if (
            not self.reviewed
            or not self.citation.strip()
            or self.effective_to <= self.effective_from
        ):
            msg = "Rule requires review, citation and a nonempty effective period"
            raise ValueError(msg)
        if self.tiers[0].starts_at_hours != 0 or any(
            b.starts_at_hours <= a.starts_at_hours
            for a, b in zip(self.tiers, self.tiers[1:], strict=False)
        ):
            msg = "Tier thresholds must start at zero and strictly increase"
            raise ValueError(msg)
        return self


class DailyHistory(BaseModel):
    """Caller-supplied complete daily eligible overtime history."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    prior_hours: Decimal = Field(ge=0, allow_inf_nan=False)
    complete: bool


@dataclass(frozen=True)
class DailyTierAdjustment:
    """An exact duration and signed adjustment for a single tier."""

    tier_start: Decimal
    multiplier: Decimal
    hours: Fraction
    adjustment: Fraction


@dataclass(frozen=True)
class CappedOvertimeResult:
    """Retain the original base ledger and the independently auditable adjustment."""

    base: ConditionCostResult
    rule: CappedDailyRule
    prior_overtime_hours: Decimal
    effective_salary_basis: Fraction
    adjustments: tuple[DailyTierAdjustment, ...]
    total: Fraction
    time_off_hours: Fraction = Fraction(0)
    time_off_cash: Fraction | None = None


def cost_capped_daily_overtime(
    release: ConditionRelease,
    rule: CappedDailyRule,
    activity: Activity,
    local_timezone: str,
    history: DailyHistory,
) -> CappedOvertimeResult:
    """Replace counted salary for explicit overtime; retain other base components.

    The caller establishes eligibility, the applicable day/rate schedule and cash
    choice. An explicit time-off multiplier replaces cash tiers and grants one
    hour of leave credit per worked hour. Holiday precedence, recall grouping
    and rounding require separate review.
    The supplied cap and source must apply to the identified worker and day.
    """
    release = ConditionRelease.model_validate(release.model_dump())
    rule = CappedDailyRule.model_validate(rule.model_dump())
    activity = Activity.model_validate(activity.model_dump())
    history = DailyHistory.model_validate(history.model_dump())
    if not history.complete:
        msg = "Complete nonnegative daily overtime history is required"
        raise ValueError(msg)
    if activity.resources != Decimal(1):
        msg = "Capped overtime requires one resource"
        raise ValueError(msg)
    zone = ZoneInfo(local_timezone)
    start = activity.starts_at.astimezone(UTC)
    end = activity.ends_at.astimezone(UTC)
    day = start.astimezone(zone).date()
    if (end - timedelta(microseconds=1)).astimezone(zone).date() != day:
        msg = "Capped overtime cannot span local calendar dates"
        raise ValueError(msg)
    if not rule.effective_from <= day < rule.effective_to:
        msg = "Capped overtime rule does not cover activity date"
        raise ValueError(msg)
    source = release.sources.require_applicable(
        rule.source_id,
        day,
        release.jurisdiction,
        release.employer,
        release.classification,
    )
    if source.sha256 != rule.source_sha256:
        msg = "Capped overtime source hash mismatch"
        raise ValueError(msg)
    base = cost_condition_activity(release, activity, local_timezone)
    current = [
        c for c in release.conditions if c.effective_from <= day < c.effective_to
    ]
    salary = next(c for c in current if c.kind == "salary")
    if salary.included_components:
        msg = "Capped overtime requires salary without bundled components"
        raise ValueError(msg)
    paid_hours = next(c for c in current if c.kind == "paid_hours")
    salary_rate = Fraction(salary.value) / Fraction(paid_hours.value)
    basis = min(salary_rate, Fraction(rule.salary_cap_hourly))
    elapsed = end - start
    micros = (elapsed.days * 86400 + elapsed.seconds) * 1000000 + elapsed.microseconds
    remaining = Fraction(micros, 3600000000)
    exact_base = Fraction(base.exact_total_numerator, base.exact_total_denominator)
    if (multiplier := rule.time_off_cash_multiplier) is not None:
        cash = remaining * basis * Fraction(multiplier)
        adjustment = cash - remaining * salary_rate
        return CappedOvertimeResult(
            base,
            rule,
            history.prior_hours,
            basis,
            (DailyTierAdjustment(Decimal(0), multiplier, remaining, adjustment),),
            exact_base + adjustment,
            time_off_hours=remaining,
            time_off_cash=cash,
        )
    adjustments = _cash_adjustments(
        rule,
        remaining,
        Fraction(history.prior_hours),
        basis,
        salary_rate,
    )
    return CappedOvertimeResult(
        base,
        rule,
        history.prior_hours,
        basis,
        adjustments,
        exact_base + sum((x.adjustment for x in adjustments), Fraction(0)),
    )


def _cash_adjustments(
    rule: CappedDailyRule,
    remaining: Fraction,
    cumulative: Fraction,
    basis: Fraction,
    salary_rate: Fraction,
) -> tuple[DailyTierAdjustment, ...]:
    adjustments: list[DailyTierAdjustment] = []
    for index, tier in enumerate(rule.tiers):
        if remaining <= 0:
            break
        next_threshold = (
            Fraction(rule.tiers[index + 1].starts_at_hours)
            if index + 1 < len(rule.tiers)
            else None
        )
        if next_threshold is not None and cumulative >= next_threshold:
            continue
        hours = (
            remaining
            if next_threshold is None
            else min(remaining, next_threshold - cumulative)
        )
        adjustment = hours * (basis * Fraction(tier.multiplier) - salary_rate)
        adjustments.append(
            DailyTierAdjustment(
                tier.starts_at_hours,
                tier.multiplier,
                hours,
                adjustment,
            ),
        )
        remaining -= hours
        cumulative += hours
    return tuple(adjustments)
