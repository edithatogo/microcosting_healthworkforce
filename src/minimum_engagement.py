# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""One explicitly eligible minimum engagement with declared pay components."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Self
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.conditions import ConditionRelease, cost_condition_activity, hourly_components
from src.costing import Activity


class MinimumEngagementRule(BaseModel):
    """A reviewed and scoped minimum with explicit component inclusions."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    rule_id: str = Field(min_length=1)
    minimum_hours: Decimal = Field(gt=0, allow_inf_nan=False)
    included_components: tuple[str, ...] = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation: str = Field(min_length=1)
    effective_from: date
    effective_to: date
    reviewed: bool
    eligibility_confirmed: bool

    @model_validator(mode="after")
    def valid_rule(self) -> Self:
        """Require reviewed eligibility, unique components and bounded dates."""
        if not self.reviewed or not self.eligibility_confirmed:
            msg = "Minimum engagement review and eligibility must be confirmed"
            raise ValueError(msg)
        if not self.citation.strip() or self.effective_to <= self.effective_from:
            msg = "Minimum engagement needs a citation and effective dates"
            raise ValueError(msg)
        if len(set(self.included_components)) != len(self.included_components) or any(
            not item.strip() for item in self.included_components
        ):
            msg = "Minimum engagement components must be unique and nonempty"
            raise ValueError(msg)
        return self


class MinimumEngagementResult(BaseModel):
    """Worked and additional guaranteed pay, with explicit source provenance."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    release_id: str
    method_id: str = "minimum_engagement_components_v1"
    activity_id: str
    starts_at: datetime
    ends_at: datetime
    worked_hours: Decimal
    paid_minimum_hours: Decimal
    worked_cost: Decimal
    minimum_increment: Decimal
    total: Decimal
    included_components: tuple[str, ...]
    condition_ids: tuple[str, ...]
    rule_id: str
    source_id: str
    source_sha256: str
    citation: str


def cost_minimum_engagement(
    release: ConditionRelease,
    rule: MinimumEngagementRule,
    activity: Activity,
    local_timezone: str,
) -> MinimumEngagementResult:
    """Price one local-day engagement without assuming interaction with premiums.

    The caller confirms eligibility and the components included in the minimum.
    Additional guaranteed hours are priced at the activity's local-day rates;
    there is no inferred timing, overtime, premium stacking or rounding.
    """
    release = ConditionRelease.model_validate(release.model_dump())
    rule = MinimumEngagementRule.model_validate(rule.model_dump())
    activity = Activity.model_validate(activity.model_dump())
    zone = ZoneInfo(local_timezone)
    if activity.resources != Decimal(1):
        msg = "Minimum engagement requires exactly one resource"
        raise ValueError(msg)
    day = activity.starts_at.astimezone(UTC).astimezone(zone).date()
    final_day = (
        (activity.ends_at.astimezone(UTC) - timedelta(microseconds=1))
        .astimezone(zone)
        .date()
    )
    if final_day != day:
        msg = "Minimum engagement cannot span local calendar dates"
        raise ValueError(msg)
    if not rule.effective_from <= day < rule.effective_to:
        msg = "Minimum engagement rule does not cover activity date"
        raise ValueError(msg)
    source = release.sources.require_applicable(
        rule.source_id,
        day,
        release.jurisdiction,
        release.employer,
        release.classification,
    )
    if source.sha256 != rule.source_sha256:
        msg = "Minimum engagement rule source hash mismatch"
        raise ValueError(msg)
    rates = hourly_components(release, day)
    if not set(rule.included_components).issubset(rates):
        msg = "Minimum engagement references an unknown component"
        raise ValueError(msg)
    result = cost_condition_activity(release, activity, local_timezone)
    worked_hours = sum((segment.hours for segment in result.segments), Decimal(0))
    guaranteed_hours = max(worked_hours, rule.minimum_hours)
    increment = (guaranteed_hours - worked_hours) * sum(
        (rates[name] for name in rule.included_components),
        Decimal(0),
    )
    return MinimumEngagementResult(
        release_id=release.release_id,
        activity_id=activity.activity_id,
        starts_at=activity.starts_at,
        ends_at=activity.ends_at,
        worked_hours=worked_hours,
        paid_minimum_hours=guaranteed_hours,
        worked_cost=result.total,
        minimum_increment=increment,
        total=result.total + increment,
        included_components=rule.included_components,
        condition_ids=result.segments[0].condition_ids,
        rule_id=rule.rule_id,
        source_id=rule.source_id,
        source_sha256=rule.source_sha256,
        citation=rule.citation,
    )
