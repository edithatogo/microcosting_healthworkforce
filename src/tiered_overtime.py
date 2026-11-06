# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Explicit nondecreasing cumulative overtime tiers for one supplied pay period."""

from decimal import Decimal
from typing import Self
lazy from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.roster_costing import (
    OvertimeRule,
    PayPeriod,
    RosterCostRow,
    cost_overtime_period,
)
lazy from src.conditions import ConditionRelease
lazy from src.costing import Activity


class OvertimeTier(BaseModel):
    """A threshold and its total salary multiplier, both explicitly supplied."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    threshold_hours: Decimal = Field(ge=0, allow_inf_nan=False)
    multiplier: Decimal = Field(ge=1, allow_inf_nan=False)


class TieredOvertimeRule(BaseModel):
    """A dated, reviewed and source-linked series of cumulative thresholds."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    rule_id: str = Field(min_length=1)
    tiers: tuple[OvertimeTier, ...] = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation: str = Field(min_length=1)
    effective_from: date
    effective_to: date
    reviewed: bool

    @model_validator(mode="after")
    def valid_tiers(self) -> Self:
        """Reject decreasing or duplicate thresholds and decreasing multipliers."""
        for previous, current in zip(self.tiers, self.tiers[1:], strict=False):
            if (
                current.threshold_hours <= previous.threshold_hours
                or current.multiplier < previous.multiplier
            ):
                msg = "Overtime tiers must increase without lowering rates"
                raise ValueError(msg)
        return self


class TierPremium(BaseModel):
    """An additive increment above one threshold, not an exclusive band."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    threshold_hours: Decimal
    total_multiplier: Decimal
    incremental_multiplier: Decimal
    hours_at_or_above: Decimal
    premium: Decimal
    rows: tuple[RosterCostRow, ...]


class TieredOvertimeResult(BaseModel):
    """Base components counted once, with incremental tier premiums and lineage."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    release_id: str
    rule_id: str
    method_id: str = "cumulative_salary_overtime_tiers_v1"
    base_cost: Decimal
    total: Decimal
    tiers: tuple[TierPremium, ...]


def cost_tiered_overtime(
    release: ConditionRelease,
    period: PayPeriod,
    rule: TieredOvertimeRule,
    activities: tuple[Activity, ...],
    local_timezone: str,
) -> TieredOvertimeResult:
    """Add salary premium increments above each nondecreasing tier threshold.

    Threshold hours are cumulative, so a later tier's hours are also included in
    earlier tier hours. Base salary and other base components are counted once.
    Eligibility, award interpretation, pay-period completeness and premium stacking
    remain explicit caller assertions as for the underlying overtime method.
    """
    rule = TieredOvertimeRule.model_validate(rule.model_dump())
    tiers: list[TierPremium] = []
    base: Decimal | None = None
    previous = Decimal(1)
    for tier in rule.tiers:
        incremental = tier.multiplier - previous
        single = OvertimeRule(
            rule_id=rule.rule_id,
            threshold_hours=tier.threshold_hours,
            multiplier=Decimal(1) + incremental,
            source_id=rule.source_id,
            source_sha256=rule.source_sha256,
            citation=rule.citation,
            effective_from=rule.effective_from,
            effective_to=rule.effective_to,
            reviewed=rule.reviewed,
        )
        result = cost_overtime_period(
            release,
            period,
            single,
            activities,
            local_timezone,
        )
        premium = sum((row.overtime_increment for row in result.rows), Decimal(0))
        if base is None:
            base = result.total - premium
        tiers.append(
            TierPremium(
                threshold_hours=tier.threshold_hours,
                total_multiplier=tier.multiplier,
                incremental_multiplier=incremental,
                hours_at_or_above=result.overtime_hours,
                premium=premium,
                rows=result.rows,
            ),
        )
        previous = tier.multiplier
    if base is None:
        msg = "At least one overtime tier is required"
        raise ValueError(msg)
    return TieredOvertimeResult(
        release_id=release.release_id,
        rule_id=rule.rule_id,
        base_cost=base,
        total=base + sum((tier.premium for tier in tiers), Decimal(0)),
        tiers=tuple(tiers),
    )
