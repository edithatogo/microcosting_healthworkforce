# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Explicit minimum engagement and worked-hours overtime composition."""

from decimal import Decimal
from fractions import Fraction
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.minimum_engagement import MinimumEngagementRule, cost_minimum_engagement
from src.roster_costing import OvertimeRule, PayPeriod, cost_overtime_period
lazy from src.conditions import ConditionRelease
lazy from src.costing import Activity


class InteractionResult(BaseModel):
    """Keep the two reviewed rule results and the exact combined amount."""

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)
    method: Literal["worked_overtime_ordinary_minimum_v1"]
    minimum_total: Decimal
    overtime_increment: Decimal
    total: Decimal
    exact_total_numerator: int
    exact_total_denominator: int = Field(gt=0)
    minimum_rule_id: str
    overtime_rule_id: str
    minimum_source_id: str
    minimum_source_sha256: str
    minimum_citation: str
    overtime_source_id: str
    overtime_source_sha256: str
    overtime_citation: str


class InteractionRules(BaseModel):
    """Require the caller to select a supported, reviewed interaction."""

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)
    method: Literal["worked_overtime_ordinary_minimum_v1"]
    minimum: MinimumEngagementRule
    overtime: OvertimeRule


def cost_minimum_with_overtime(
    release: ConditionRelease,
    period: PayPeriod,
    rules: InteractionRules,
    activity: Activity,
    local_timezone: str,
) -> InteractionResult:
    """Apply overtime to worked time and pay minimum top-up at ordinary rates.

    The caller must explicitly select and substantiate this interaction. It does
    not treat unworked guaranteed hours as overtime-eligible work.
    """
    rules = InteractionRules.model_validate(rules.model_dump())
    minimum = rules.minimum
    overtime = rules.overtime
    guaranteed = cost_minimum_engagement(release, minimum, activity, local_timezone)
    worked = cost_overtime_period(
        release,
        period,
        overtime,
        (activity,),
        local_timezone,
    )
    increment = sum((row.overtime_increment for row in worked.rows), Decimal(0))
    exact = Fraction(
        guaranteed.exact_total_numerator,
        guaranteed.exact_total_denominator,
    )
    exact += Fraction(worked.exact_premium_numerator, worked.exact_premium_denominator)
    return InteractionResult(
        method=rules.method,
        minimum_total=guaranteed.total,
        overtime_increment=increment,
        total=guaranteed.total + increment,
        exact_total_numerator=exact.numerator,
        exact_total_denominator=exact.denominator,
        minimum_rule_id=minimum.rule_id,
        overtime_rule_id=overtime.rule_id,
        minimum_source_id=minimum.source_id,
        minimum_source_sha256=minimum.source_sha256,
        minimum_citation=minimum.citation,
        overtime_source_id=overtime.source_id,
        overtime_source_sha256=overtime.source_sha256,
        overtime_citation=overtime.citation,
    )
