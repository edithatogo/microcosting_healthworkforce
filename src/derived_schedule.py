# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Explicit effective-dated versions of additive derived cost rules."""

from fractions import Fraction
from itertools import pairwise
from typing import Self
from zoneinfo import ZoneInfo
lazy from datetime import date
lazy from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.conditions import ConditionRelease, cost_condition_activity
from src.costing import Activity
from src.derived_components import (
    DerivedComponentRule,
    DerivedCost,
    DerivedRow,
    cost_derived_snapshot,
)


class RuleSeries(BaseModel):
    """Non-overlapping editions for one explicitly required component."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    component: str = Field(min_length=1)
    editions: tuple[DerivedComponentRule, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_editions(self) -> Self:
        """Reject changed components, duplicate identities and overlaps."""
        if not self.component.strip() or any(
            item.component != self.component for item in self.editions
        ):
            msg = "Rule editions require one component"
            raise ValueError(msg)
        if len({item.rule_id for item in self.editions}) != len(self.editions):
            msg = "Duplicate derived rule identity"
            raise ValueError(msg)
        ordered = sorted(self.editions, key=lambda item: item.effective_from)
        if any(a.effective_to > b.effective_from for a, b in pairwise(ordered)):
            msg = "Derived rule editions overlap"
            raise ValueError(msg)
        return self


class DerivedSchedule(BaseModel):
    """Ordered required components; order defines their dependency sequence."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    series: tuple[RuleSeries, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_series(self) -> Self:
        """Avoid ambiguous component and rule identities across the schedule."""
        if len({item.component for item in self.series}) != len(self.series):
            msg = "Duplicate scheduled component"
            raise ValueError(msg)
        ids = [rule.rule_id for item in self.series for rule in item.editions]
        if len(set(ids)) != len(ids):
            msg = "Duplicate scheduled rule identity"
            raise ValueError(msg)
        return self

    def select(self, when: date) -> tuple[DerivedComponentRule, ...]:
        """Select one edition per required component, never filling gaps."""
        schedule = DerivedSchedule.model_validate(self.model_dump())
        selected: list[DerivedComponentRule] = []
        for item in schedule.series:
            match = [
                r for r in item.editions if r.effective_from <= when < r.effective_to
            ]
            if len(match) != 1:
                msg = "Scheduled component lacks one rule for the costing date"
                raise ValueError(msg)
            selected.append(match[0])
        return tuple(selected)


def cost_scheduled_snapshot(
    release: ConditionRelease,
    when: date,
    hours: Decimal,
    schedule: DerivedSchedule,
) -> DerivedCost:
    """Price a snapshot using the supplied effective-dated rule series."""
    return cost_derived_snapshot(release, when, hours, schedule.select(when))


def cost_scheduled_activity(
    release: ConditionRelease,
    activity: Activity,
    timezone: str,
    schedule: DerivedSchedule,
) -> DerivedCost:
    """Price each local-day segment using its own explicitly selected rules."""
    release = ConditionRelease.model_validate(release.model_dump())
    activity = Activity.model_validate(activity.model_dump())
    schedule = DerivedSchedule.model_validate(schedule.model_dump())
    base = cost_condition_activity(release, activity, timezone)
    zone = ZoneInfo(timezone)
    rows: list[DerivedRow] = []
    for segment in base.segments:
        elapsed = segment.ends_at - segment.starts_at
        micros = (
            elapsed.days * 86400 + elapsed.seconds
        ) * 1000000 + elapsed.microseconds
        hours = Fraction(micros, 3600000000) * Fraction(activity.resources)
        day = segment.starts_at.astimezone(zone).date()
        hourly = cost_derived_snapshot(release, day, Decimal(1), schedule.select(day))
        rows.extend(
            DerivedRow(
                day,
                row.rule,
                row.base_hourly,
                row.hourly_amount,
                hours,
                row.hourly_amount * hours,
            )
            for row in hourly.rows
        )
    total = Fraction(base.exact_total_numerator, base.exact_total_denominator)
    return DerivedCost(
        base,
        tuple(rows),
        total + sum((r.amount for r in rows), Fraction(0)),
    )
