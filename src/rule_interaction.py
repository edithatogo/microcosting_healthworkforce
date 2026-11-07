# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Explicit minimum engagement and worked-hours overtime composition."""

from datetime import UTC, date
from decimal import Decimal
from fractions import Fraction
from typing import Literal, Self
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.minimum_engagement import (
    MinimumEngagementResult,
    MinimumEngagementRule,
    cost_minimum_engagement,
)
from src.roster_costing import (
    OvertimeRule,
    PayPeriod,
    RosterCostResult,
    cost_overtime_period,
)
lazy from src.conditions import ConditionRelease
lazy from src.costing import Activity


class InteractionResult(BaseModel):
    """Keep the two reviewed rule results and the exact combined amount."""

    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)
    method: Literal["worked_overtime_ordinary_minimum_v1"]
    minimum_result: MinimumEngagementResult
    overtime_result: RosterCostResult
    minimum_total: Decimal
    overtime_increment: Decimal
    total: Decimal
    exact_total_numerator: int
    exact_total_denominator: int = Field(gt=0)
    interaction_rule_id: str
    interaction_source_id: str
    interaction_source_sha256: str
    interaction_citation: str
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
    rule_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation: str = Field(min_length=1)
    effective_from: date
    effective_to: date
    reviewed: bool

    @model_validator(mode="after")
    def validate_interaction(self) -> Self:
        """Require an independently reviewed, bounded interaction assertion."""
        if (
            not self.reviewed
            or not self.citation.strip()
            or self.effective_to <= self.effective_from
        ):
            msg = "Interaction requires review, citation and effective dates"
            raise ValueError(msg)
        return self


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
    day = activity.starts_at.astimezone(UTC).astimezone(ZoneInfo(local_timezone)).date()
    if not rules.effective_from <= day < rules.effective_to:
        msg = "Interaction rule does not cover activity date"
        raise ValueError(msg)
    source = release.sources.require_applicable(
        rules.source_id,
        day,
        release.jurisdiction,
        release.employer,
        release.classification,
    )
    if source.sha256 != rules.source_sha256:
        msg = "Interaction source hash mismatch"
        raise ValueError(msg)
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
    premium = Fraction(worked.exact_premium_numerator, worked.exact_premium_denominator)
    exact = Fraction(
        guaranteed.exact_total_numerator,
        guaranteed.exact_total_denominator,
    )
    exact += premium
    return InteractionResult(
        method=rules.method,
        minimum_result=guaranteed,
        overtime_result=worked,
        minimum_total=guaranteed.total,
        overtime_increment=Decimal(premium.numerator) / premium.denominator,
        total=Decimal(exact.numerator) / exact.denominator,
        exact_total_numerator=exact.numerator,
        exact_total_denominator=exact.denominator,
        interaction_rule_id=rules.rule_id,
        interaction_source_id=rules.source_id,
        interaction_source_sha256=rules.source_sha256,
        interaction_citation=rules.citation,
        minimum_rule_id=minimum.rule_id,
        overtime_rule_id=overtime.rule_id,
        minimum_source_id=minimum.source_id,
        minimum_source_sha256=minimum.source_sha256,
        minimum_citation=minimum.citation,
        overtime_source_id=overtime.source_id,
        overtime_source_sha256=overtime.source_sha256,
        overtime_citation=overtime.citation,
    )
