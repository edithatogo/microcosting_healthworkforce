# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Versioned, explicitly reviewed conditions and limited hourly costing rules."""

from datetime import UTC, date, datetime, time, timedelta
from fractions import Fraction
from typing import Literal, Self
from zoneinfo import ZoneInfo
lazy from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

lazy from src.costing import Activity
lazy from src.pay_period_effective import RetrospectiveAuthority
lazy from src.source_registry import SourceRegistry

ConditionKind = Literal["salary", "paid_hours", "fixed_annual", "salary_fraction"]
ConditionUnit = Literal["AUD/year", "hours/year", "fraction"]


class WorkbookConditionOrigin(BaseModel):
    """Reviewed applicability of a workbook cell proposed as a condition."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    workbook_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    sheet: str = Field(min_length=1)
    coordinate: str = Field(pattern=r"^[A-Z]{1,3}[1-9][0-9]*$")
    applicability: Literal["verified", "unresolved", "conflicting"]
    review_evidence: str = Field(min_length=1)


class PayrollSalaryDivisor(BaseModel):
    """Exact annual divisor sourced by the enclosing salary condition."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    numerator: int = Field(gt=0)
    denominator: int = Field(gt=0)


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
    retrospective: RetrospectiveAuthority | None = None
    included_components: tuple[str, ...] = ()
    workbook_origin: WorkbookConditionOrigin | None = None
    payroll_salary_divisor: PayrollSalaryDivisor | None = None

    @model_validator(mode="after")
    def valid_condition(self) -> Self:
        """Match rule kind to units and enforce bounded, nonempty periods."""
        units: dict[ConditionKind, ConditionUnit] = {
            "salary": "AUD/year",
            "paid_hours": "hours/year",
            "fixed_annual": "AUD/year",
            "salary_fraction": "fraction",
        }
        if self.payroll_salary_divisor is not None and self.kind != "salary":
            msg = "Payroll divisor requires a salary condition"
            raise ValueError(msg)
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
        if (
            (self.included_components and self.kind != "salary")
            or any(
                not name.strip() or name == self.component
                for name in self.included_components
            )
            or len(set(self.included_components)) != len(self.included_components)
        ):
            msg = "Included components require distinct named salary inclusions"
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
    as_known_at: date | None = None
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
            origin = item.workbook_origin
            if origin is not None and (
                origin.applicability != "verified" or not origin.review_evidence.strip()
            ):
                msg = "Workbook conditions require verified cell applicability"
                raise ValueError(msg)
            self._validate_source(item)
        for index, left in enumerate(self.conditions):
            for right in self.conditions[index + 1 :]:
                overlap = (
                    left.effective_from < right.effective_to
                    and right.effective_from < left.effective_to
                )
                if overlap and left.component == right.component:
                    msg = "Overlapping condition component periods"
                    raise ValueError(msg)
                if overlap and (
                    left.component in right.included_components
                    or right.component in left.included_components
                ):
                    msg = "Separate condition duplicates a salary inclusion"
                    raise ValueError(msg)
                if overlap and set(left.included_components).intersection(
                    right.included_components,
                ):
                    msg = "Overlapping salaries duplicate an included component"
                    raise ValueError(msg)
        return self

    def _validate_source(self, item: Condition) -> None:
        """Check the source at knowledge dates and the entire entitlement interval."""
        authority = item.retrospective
        dates = (item.effective_from, item.effective_to - timedelta(days=1))
        if authority is not None:
            if self.as_known_at is None or authority.as_known_at != self.as_known_at:
                msg = "Retrospective conditions require the release knowledge date"
                raise ValueError(msg)
            if item.effective_from < authority.known_from and (
                item.effective_from < authority.entitlement_from
                or min(item.effective_to, authority.known_from)
                > authority.entitlement_to
            ):
                msg = "Date outside reviewed retrospective entitlement interval"
                raise ValueError(msg)
            dates += (authority.known_from, self.as_known_at)
        for when in dates:
            if authority is not None and when < authority.known_from:
                if not authority.entitlement_from <= when < authority.entitlement_to:
                    msg = "Date outside reviewed retrospective entitlement interval"
                    raise ValueError(msg)
                continue
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
    divisor = salary.payroll_salary_divisor
    numerator = paid_hours.value if divisor is None else Decimal(divisor.numerator)
    denominator = 1 if divisor is None else divisor.denominator
    result = {salary.component: salary.value * denominator / numerator}
    for item in current:
        if item.kind == "fixed_annual":
            result[item.component] = item.value / paid_hours.value
        elif item.kind == "salary_fraction":
            result[item.component] = salary.value * item.value * denominator / numerator
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
    exact_total_numerator: int
    exact_total_denominator: int = Field(gt=0)
    segments: tuple[ConditionCostSegment, ...]


def exact_hourly_components(
    release: ConditionRelease,
    when: date,
    *,
    use_payroll_basis: bool = True,
) -> dict[str, Fraction]:
    """Keep annual condition ratios exact until the caller chooses rounding."""
    release = ConditionRelease.model_validate(release.model_dump())
    current = [
        c for c in release.conditions if c.effective_from <= when < c.effective_to
    ]
    salaries = [c for c in current if c.kind == "salary"]
    hours = [c for c in current if c.kind == "paid_hours"]
    if len(salaries) != 1 or len(hours) != 1:
        msg = "Exactly one salary and paid-hours condition must cover the date"
        raise ValueError(msg)
    salary = Fraction(salaries[0].value)
    annual_hours = Fraction(hours[0].value)
    divisor = salaries[0].payroll_salary_divisor
    salary_hours = (
        Fraction(divisor.numerator, divisor.denominator)
        if use_payroll_basis and divisor is not None
        else annual_hours
    )
    components = {salaries[0].component: salary / salary_hours}
    for item in current:
        if item.kind == "fixed_annual":
            components[item.component] = Fraction(item.value) / annual_hours
        elif item.kind == "salary_fraction":
            components[item.component] = salary * Fraction(item.value) / salary_hours
    return components


class SnapshotQuantity(BaseModel):
    """Explicit nonnegative resource hours for a dated static calculation."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    hours: Decimal = Field(ge=0, allow_inf_nan=False)


class ConditionSnapshotResult(BaseModel):
    """Static component ledger and the accepted inputs used to calculate it."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    release_id: str
    method_id: str
    jurisdiction: str
    employer: str
    classification: str
    currency: Literal["AUD"] = "AUD"
    as_of: date
    hours: Decimal
    components: dict[str, Decimal]
    total: Decimal
    exact_total_numerator: int
    exact_total_denominator: int = Field(gt=0)
    conditions: tuple[Condition, ...]


def cost_condition_snapshot(
    release: ConditionRelease,
    when: date,
    hours: Decimal,
) -> ConditionSnapshotResult:
    """Price supplied paid hours at one date, without inferring eligibility.

    This is a nominal-hour scenario: it does not add leave, overtime or cover.
    Source and reviewer assertions in the release must be independently qualified.
    """
    release = ConditionRelease.model_validate(release.model_dump())
    quantity = SnapshotQuantity(hours=hours)
    rates = hourly_components(release, when)
    components = {name: rate * quantity.hours for name, rate in rates.items()}
    exact = sum(
        exact_hourly_components(release, when).values(),
        Fraction(0),
    ) * Fraction(quantity.hours)
    return ConditionSnapshotResult(
        release_id=release.release_id,
        method_id=release.method_id,
        jurisdiction=release.jurisdiction,
        employer=release.employer,
        classification=release.classification,
        as_of=when,
        hours=quantity.hours,
        components=components,
        total=sum(components.values(), Decimal(0)),
        exact_total_numerator=exact.numerator,
        exact_total_denominator=exact.denominator,
        conditions=tuple(
            c for c in release.conditions if c.effective_from <= when < c.effective_to
        ),
    )


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
    exact_total = Fraction(0)
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
        microseconds = (
            duration.days * 86400 + duration.seconds
        ) * 1000000 + duration.microseconds
        exact_hours = Fraction(microseconds, 3600000000) * Fraction(activity.resources)
        exact_total += (
            sum(exact_hourly_components(release, day).values(), Fraction(0))
            * exact_hours
        )
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
        exact_total_numerator=exact_total.numerator,
        exact_total_denominator=exact_total.denominator,
        segments=tuple(segments),
    )
