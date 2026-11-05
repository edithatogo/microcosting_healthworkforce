# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Versioned, explicitly reviewed conditions and limited hourly costing rules."""

from datetime import UTC, date, datetime, time, timedelta
from typing import Literal, Self
from zoneinfo import ZoneInfo
lazy from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

lazy from src.costing import Activity
lazy from src.source_registry import SourceRegistry

ConditionKind = Literal["salary", "paid_hours", "fixed_annual", "salary_fraction"]
ConditionUnit = Literal["AUD/year", "hours/year", "fraction"]


class Condition(BaseModel):
    """A single versioned condition; acceptance is an explicit reviewer assertion."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    condition_id: str = Field(min_length=1)
    kind: ConditionKind
    component: str = Field(min_length=1)
    value: Decimal = Field(ge=0, allow_inf_nan=False)
    unit: ConditionUnit
    effective_from: date
    effective_to: date
    source_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation: str = Field(min_length=1)
    status: Literal["candidate", "accepted", "rejected"]

    @model_validator(mode="after")
    def valid_condition(self) -> Self:
        """Match rule kind to units and enforce bounded, nonempty periods."""
        units: dict[ConditionKind, ConditionUnit] = {
            "salary": "AUD/year",
            "paid_hours": "hours/year",
            "fixed_annual": "AUD/year",
            "salary_fraction": "fraction",
        }
        if self.unit != units[self.kind]:
            msg = "Condition unit does not match its rule kind"
            raise ValueError(msg)
        if self.effective_to <= self.effective_from:
            msg = "Condition period must be nonempty"
            raise ValueError(msg)
        if not self.citation.strip():
            msg = "Condition citation is required"
            raise ValueError(msg)
        if self.kind == "paid_hours" and self.value == 0:
            msg = "Paid hours must be positive"
            raise ValueError(msg)
        return self


class ConditionRelease(BaseModel):
    """A frozen scoped release of reviewed conditions and source declarations."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    schema_version: Literal[1] = 1
    release_id: str = Field(min_length=1)
    method_id: Literal["annual_salary_components_v1"] = "annual_salary_components_v1"
    jurisdiction: str = Field(min_length=1)
    employer: str = Field(min_length=1)
    classification: str = Field(min_length=1)
    sources: SourceRegistry
    conditions: tuple[Condition, ...]

    @model_validator(mode="after")
    def validate_release(self) -> Self:
        """Reject unaccepted, conflicting or inadequately scoped source assertions."""
        ids: set[str] = set()
        for item in self.conditions:
            if item.condition_id in ids:
                msg = "Duplicate condition identity"
                raise ValueError(msg)
            ids.add(item.condition_id)
            if item.status != "accepted":
                msg = "Costing releases require accepted conditions"
                raise ValueError(msg)
            for when in (item.effective_from, item.effective_to - timedelta(days=1)):
                source = self.sources.require_applicable(
                    item.source_id,
                    when,
                    self.jurisdiction,
                    self.employer,
                    self.classification,
                )
                if source.sha256 != item.source_sha256:
                    msg = "Condition source hash mismatch"
                    raise ValueError(msg)
        for index, left in enumerate(self.conditions):
            for right in self.conditions[index + 1 :]:
                if (
                    left.component == right.component
                    and left.effective_from < right.effective_to
                    and right.effective_from < left.effective_to
                ):
                    msg = "Overlapping condition component periods"
                    raise ValueError(msg)
        return self


def hourly_components(release: ConditionRelease, when: date) -> dict[str, Decimal]:
    """Apply salary-only fractions and explicit annual amounts per paid hour.

    No other component is included in the fraction base, and this rule does not
    determine whether a condition applies to a particular worker or shift.
    """
    release = ConditionRelease.model_validate(release.model_dump())
    current = [
        c for c in release.conditions if c.effective_from <= when < c.effective_to
    ]
    salaries = [c for c in current if c.kind == "salary"]
    hours = [c for c in current if c.kind == "paid_hours"]
    if len(salaries) != 1 or len(hours) != 1:
        msg = "Exactly one salary and paid-hours condition must cover the date"
        raise ValueError(msg)
    salary, paid_hours = salaries[0], hours[0]
    result = {salary.component: salary.value / paid_hours.value}
    for item in current:
        if item.kind == "fixed_annual":
            result[item.component] = item.value / paid_hours.value
        elif item.kind == "salary_fraction":
            result[item.component] = salary.value * item.value / paid_hours.value
    return result


class ConditionCostSegment(BaseModel):
    """One local-day activity segment with all input condition identities."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    starts_at: datetime
    ends_at: datetime
    hours: Decimal
    condition_ids: tuple[str, ...]
    components: dict[str, Decimal]


class ConditionCostResult(BaseModel):
    """A dated condition-cost result; source citations remain in its release."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    release_id: str
    method_id: str
    activity_id: str
    resource_id: str
    timezone: str
    total: Decimal
    segments: tuple[ConditionCostSegment, ...]


def cost_condition_activity(
    release: ConditionRelease,
    activity: Activity,
    local_timezone: str,
) -> ConditionCostResult:
    """Cost an activity by local calendar day using its dated conditions.

    Conditions must represent actual effective dates, including any first-full-pay-
    period qualification. This method does not infer pay cycles or overtime.
    """
    release = ConditionRelease.model_validate(release.model_dump())
    activity = Activity.model_validate(activity.model_dump())
    zone = ZoneInfo(local_timezone)
    cursor = activity.starts_at.astimezone(UTC)
    end = activity.ends_at.astimezone(UTC)
    segments: list[ConditionCostSegment] = []
    while cursor < end:
        day = cursor.astimezone(zone).date()
        next_day = datetime.combine(day + timedelta(days=1), time.min, zone).astimezone(
            UTC,
        )
        if next_day <= cursor:
            msg = "Timezone produces an unsupported calendar transition"
            raise ValueError(msg)
        stop = min(end, next_day)
        duration = stop - cursor
        seconds = Decimal(duration.days * 86400 + duration.seconds) + Decimal(
            duration.microseconds,
        ) / Decimal(1000000)
        hours = seconds / Decimal(3600) * activity.resources
        rates = hourly_components(release, day)
        active = tuple(
            c.condition_id
            for c in release.conditions
            if c.effective_from <= day < c.effective_to
        )
        segments.append(
            ConditionCostSegment(
                starts_at=cursor,
                ends_at=stop,
                hours=hours,
                condition_ids=active,
                components={name: value * hours for name, value in rates.items()},
            ),
        )
        cursor = stop
    total = sum((sum(s.components.values(), Decimal(0)) for s in segments), Decimal(0))
    return ConditionCostResult(
        release_id=release.release_id,
        method_id=release.method_id,
        activity_id=activity.activity_id,
        resource_id=activity.resource_id,
        timezone=local_timezone,
        total=total,
        segments=tuple(segments),
    )
