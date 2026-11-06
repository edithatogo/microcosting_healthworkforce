# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Explicit, evidence-scoped flat-hourly snapshot and activity costing.

This method applies supplied rates; it does not interpret industrial instruments.
Dates and source review assertions are supplied by the release author.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from fractions import Fraction
from typing import Literal, Self
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

lazy from src.source_registry import SourceRegistry


class FrozenModel(BaseModel):
    """Reject undeclared data and implicit type conversions."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class RatePeriod(FrozenModel):
    """A precomputed hourly rate, effective in a half-open time interval."""

    rate_id: str = Field(min_length=1)
    resource_id: str = Field(min_length=1)
    jurisdiction: str = Field(min_length=1)
    employer: str = Field(min_length=1)
    classification: str = Field(min_length=1)
    starts_at: datetime
    ends_at: datetime | None = None
    local_timezone: str = "UTC"
    components: dict[str, Decimal]
    source_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation: str = Field(min_length=1)
    reviewed: bool

    @field_validator("starts_at", "ends_at")
    @classmethod
    def aware(cls, value: datetime | None) -> datetime | None:
        """Normalize instants before comparisons, including DST transitions."""
        if value is not None and value.utcoffset() is None:
            msg = "Rate times must be timezone-aware"
            raise ValueError(msg)
        return value.astimezone(UTC) if value is not None else None

    @model_validator(mode="after")
    def valid_rate(self) -> Self:
        """Reject unreviewed, negative, ambiguous or empty rates."""
        ZoneInfo(self.local_timezone)
        if not self.reviewed or not self.citation.strip():
            msg = "Rate requires explicit review and citation"
            raise ValueError(msg)
        if self.ends_at is not None and self.ends_at <= self.starts_at:
            msg = "Rate interval must be nonempty"
            raise ValueError(msg)
        if not self.components or any(
            not k.strip() or not v.is_finite() or v < 0
            for k, v in self.components.items()
        ):
            msg = "Rate components must be finite nonnegative amounts"
            raise ValueError(msg)
        return self


class CostRelease(FrozenModel):
    """An explicitly versioned rate set and its declared source evidence."""

    release_id: str = Field(min_length=1)
    method_id: Literal["flat_hourly_v1"]
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    sources: SourceRegistry
    rates: tuple[RatePeriod, ...]
    required_capabilities: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_rates(self) -> Self:
        """Reject overlapping rates, conflicting resource scopes and source hashes."""
        if self.required_capabilities:
            msg = f"Unsupported costing capabilities: {self.required_capabilities}"
            raise ValueError(msg)
        ids: set[str] = set()
        scopes: dict[str, tuple[str, str, str]] = {}
        for rate in self.rates:
            if rate.rate_id in ids:
                msg = "Duplicate rate identity"
                raise ValueError(msg)
            ids.add(rate.rate_id)
            scope = (rate.jurisdiction, rate.employer, rate.classification)
            if rate.resource_id in scopes and scopes[rate.resource_id] != scope:
                msg = "Resource identity has conflicting scopes"
                raise ValueError(msg)
            scopes[rate.resource_id] = scope
            source = self.sources.require_applicable(
                rate.source_id,
                rate.starts_at.astimezone(ZoneInfo(rate.local_timezone)).date(),
                *scope,
            )
            if source.sha256 != rate.source_sha256:
                msg = "Rate source hash does not match its source edition"
                raise ValueError(msg)
        for i, left in enumerate(self.rates):
            for right in self.rates[i + 1 :]:
                if left.resource_id == right.resource_id and (
                    (left.ends_at is None or right.starts_at < left.ends_at)
                    and (right.ends_at is None or left.starts_at < right.ends_at)
                ):
                    msg = "Overlapping rates for a resource"
                    raise ValueError(msg)
        return self


class ResourceUse(FrozenModel):
    """An explicit quantity of resource hours at a snapshot instant."""

    resource_id: str = Field(min_length=1)
    hours: Decimal = Field(ge=0, allow_inf_nan=False)


class Activity(FrozenModel):
    """An activity with elapsed-time resource quantity; no implicit roster rules."""

    activity_id: str = Field(min_length=1)
    resource_id: str = Field(min_length=1)
    starts_at: datetime
    ends_at: datetime
    resources: Decimal = Field(ge=0, allow_inf_nan=False)
    allocation_id: str | None = None

    @model_validator(mode="after")
    def valid_interval(self) -> Self:
        """Require an unambiguous, nonempty interval."""
        if self.starts_at.utcoffset() is None or self.ends_at.utcoffset() is None:
            msg = "Activity times must be timezone-aware"
            raise ValueError(msg)
        if self.ends_at.astimezone(UTC) <= self.starts_at.astimezone(UTC):
            msg = "Activity interval must be nonempty"
            raise ValueError(msg)
        if self.allocation_id is not None:
            if not self.allocation_id.strip():
                msg = "Allocation identity cannot be blank"
                raise ValueError(msg)
            if self.resources > 1:
                msg = "An individual allocation permits at most one resource"
                raise ValueError(msg)
        return self


class CostRow(FrozenModel):
    """An auditable cost segment linked to the declared source and rate."""

    activity_id: str
    resource_id: str
    allocation_id: str | None = None
    rate_id: str
    starts_at: datetime
    ends_at: datetime | None
    hours: Decimal
    exact_hours_numerator: int = Field(ge=0)
    exact_hours_denominator: int = Field(gt=0)
    components: dict[str, Decimal]
    source_id: str
    source_sha256: str
    citation: str


class CostResult(FrozenModel):
    """Cost breakdown with method, release and source lineage."""

    release_id: str
    method_id: str
    currency: str
    total: Decimal
    exact_total_numerator: int
    exact_total_denominator: int = Field(gt=0)
    components: dict[str, Decimal]
    rows: tuple[CostRow, ...]


def _rate(release: CostRelease, resource: str, at: datetime) -> RatePeriod:
    if at.utcoffset() is None:
        msg = "Costing time must be timezone-aware"
        raise ValueError(msg)
    instant = at.astimezone(UTC)
    for rate in release.rates:
        if (
            rate.resource_id == resource
            and rate.starts_at <= instant
            and (rate.ends_at is None or instant < rate.ends_at)
        ):
            release.sources.require_applicable(
                rate.source_id,
                instant.astimezone(ZoneInfo(rate.local_timezone)).date(),
                rate.jurisdiction,
                rate.employer,
                rate.classification,
            )
            return rate
    msg = f"No rate coverage for resource {resource} at {instant.isoformat()}"
    raise ValueError(msg)


def _row(
    rate: RatePeriod,
    activity: tuple[str, str | None],
    start: datetime,
    end: datetime | None,
    hours: Fraction,
) -> CostRow:
    return CostRow(
        activity_id=activity[0],
        resource_id=rate.resource_id,
        allocation_id=activity[1],
        rate_id=rate.rate_id,
        starts_at=start,
        ends_at=end,
        hours=Decimal(hours.numerator) / Decimal(hours.denominator),
        exact_hours_numerator=hours.numerator,
        exact_hours_denominator=hours.denominator,
        components={
            key: Decimal(amount.numerator) / Decimal(amount.denominator)
            for key, value in rate.components.items()
            for amount in (Fraction(value) * hours,)
        },
        source_id=rate.source_id,
        source_sha256=rate.source_sha256,
        citation=rate.citation,
    )


def _result(release: CostRelease, rows: list[CostRow], exact: Fraction) -> CostResult:
    rates = {rate.rate_id: rate for rate in release.rates}
    component_totals: dict[str, Fraction] = {}
    for row in rows:
        hours = Fraction(row.exact_hours_numerator, row.exact_hours_denominator)
        for key, rate in rates[row.rate_id].components.items():
            component_totals[key] = (
                component_totals.get(key, Fraction(0)) + Fraction(rate) * hours
            )
    components = {
        key: Decimal(amount.numerator) / Decimal(amount.denominator)
        for key, amount in component_totals.items()
    }
    return CostResult(
        release_id=release.release_id,
        method_id=release.method_id,
        currency=release.currency,
        total=Decimal(exact.numerator) / Decimal(exact.denominator),
        exact_total_numerator=exact.numerator,
        exact_total_denominator=exact.denominator,
        components=components,
        rows=tuple(rows),
    )


def _validated(release: CostRelease) -> CostRelease:
    return CostRelease.model_validate(release.model_dump())


def cost_static(
    release: CostRelease,
    at: datetime,
    resources: tuple[ResourceUse, ...],
) -> CostResult:
    """Cost explicit resource hours at one effective instant."""
    release = _validated(release)
    resources = tuple(ResourceUse.model_validate(r.model_dump()) for r in resources)
    if len({r.resource_id for r in resources}) != len(resources):
        msg = "Duplicate static resource identity"
        raise ValueError(msg)
    rows: list[CostRow] = []
    exact = Fraction(0)
    for resource in resources:
        rate = _rate(release, resource.resource_id, at)
        rows.append(_row(rate, ("snapshot", None), at, None, Fraction(resource.hours)))
        exact += Fraction(resource.hours) * sum(
            (Fraction(value) for value in rate.components.values()),
            Fraction(0),
        )
    return _result(release, rows, exact)


def cost_dynamic(release: CostRelease, activities: tuple[Activity, ...]) -> CostResult:
    """Cost elapsed activities, rejecting overlaps for explicit allocation IDs.

    A resource ID is a shared rate category. A supplied allocation ID identifies
    one worker and must cover all their activities for overlap detection to be
    complete. Without it, parallel resource quantities remain caller-supplied.
    """
    release = _validated(release)
    activities = tuple(Activity.model_validate(a.model_dump()) for a in activities)
    if len({a.activity_id for a in activities}) != len(activities):
        msg = "Duplicate activity identity"
        raise ValueError(msg)
    allocations: dict[str, datetime] = {}
    for activity in sorted(activities, key=lambda a: a.starts_at.astimezone(UTC)):
        if activity.allocation_id is None:
            continue
        start = activity.starts_at.astimezone(UTC)
        if (
            activity.allocation_id in allocations
            and start < allocations[activity.allocation_id]
        ):
            msg = "Activities overlap for an explicit allocation identity"
            raise ValueError(msg)
        allocations[activity.allocation_id] = activity.ends_at.astimezone(UTC)
    rows: list[CostRow] = []
    exact = Fraction(0)
    for activity in activities:
        cursor = activity.starts_at.astimezone(UTC)
        end = activity.ends_at.astimezone(UTC)
        while cursor < end:
            rate = _rate(release, activity.resource_id, cursor)
            stop = min(end, rate.ends_at) if rate.ends_at is not None else end
            _rate(release, activity.resource_id, stop - timedelta(microseconds=1))
            duration = stop - cursor
            micros = (
                duration.days * 86400 + duration.seconds
            ) * 1000000 + duration.microseconds
            hours = Fraction(micros, 3600000000) * Fraction(activity.resources)
            exact += hours * sum(
                (Fraction(value) for value in rate.components.values()),
                Fraction(0),
            )
            rows.append(
                _row(
                    rate,
                    (activity.activity_id, activity.allocation_id),
                    cursor,
                    stop,
                    hours,
                ),
            )
            cursor = stop
    return _result(release, rows, exact)
