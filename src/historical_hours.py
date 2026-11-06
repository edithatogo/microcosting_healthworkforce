# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Complete-history selection of hours, separate from salary and leave payroll.

The caller selects the reviewed comparison rule, source scope, calendar convention
and exact averaging exposure. No universal weeks-per-year or payment method is
inferred. Output hours are a quantity base, not accepted individual eligibility.
"""

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
from fractions import Fraction
from typing import Literal, Self
lazy from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

lazy from src.source_registry import SourceRegistry


class HistoryModel(BaseModel):
    """Strict immutable declarations without whitespace-only identities."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    @model_validator(mode="after")
    def nonblank(self) -> Self:
        """Require meaningful identities, citations and normalization bases."""
        if any(isinstance(v, str) and not v.strip() for v in self.__dict__.values()):
            msg = "History identities, citation and basis must not be blank"
            raise ValueError(msg)
        return self


class NormalHoursRule(HistoryModel):
    """Explicitly selected twelve-month/forty-week comparison, not auto-mapped."""

    rule_id: str
    source_id: str
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation: str
    effective_from: date
    effective_to: date
    reviewed: bool
    lookback_months: Literal[12]
    minimum_service_weeks: Literal[40]
    anniversary_method: Literal["clamp_last_day_v1"]
    jurisdiction: str
    employer: str
    classification: str
    as_known_on: date
    sources: SourceRegistry

    @model_validator(mode="after")
    def bounded_rule(self) -> Self:
        """Require explicit review and a bounded operative interval."""
        if not self.reviewed or self.effective_to <= self.effective_from:
            msg = "History rule requires review and a nonempty date interval"
            raise ValueError(msg)
        return self


class HoursHistoryRequest(HistoryModel):
    """One worker/scenario with explicit current hours and averaging exposure."""

    leave_starts_on: date
    continuous_service_from: date
    continuous_service_verified: bool
    history_complete: bool
    current_hours_per_week: Decimal = Field(ge=0, allow_inf_nan=False)
    equivalent_weeks_numerator: int = Field(gt=0)
    equivalent_weeks_denominator: int = Field(gt=0)
    normalisation_kind: Literal["reviewed_payroll_exposure", "analyst_assumption"]
    normalisation_basis: str

    @model_validator(mode="after")
    def complete_declarations(self) -> Self:
        """Missing service or history cannot be silently treated as zero."""
        if not self.history_complete or not self.continuous_service_verified:
            msg = "Complete history and verified continuous service are required"
            raise ValueError(msg)
        if self.continuous_service_from >= self.leave_starts_on:
            msg = "Continuous service must start before leave"
            raise ValueError(msg)
        return self


class HistoricalHours(HistoryModel):
    """An explicitly classified total over a half-open, fully covered interval."""

    history_id: str
    starts_on: date
    ends_on: date
    hours: Decimal = Field(ge=0, allow_inf_nan=False)
    quantity_kind: Literal["observed_use", "analyst_assumption"]
    basis: str

    @model_validator(mode="after")
    def nonempty_interval(self) -> Self:
        """Reject negative/empty observation durations."""
        if self.ends_on <= self.starts_on:
            msg = "History interval must be nonempty"
            raise ValueError(msg)
        return self


@dataclass(frozen=True)
class NormalHoursSelection:
    """Exact losing/winning comparands, original evidence and selected window."""

    method_id: str
    rule: NormalHoursRule
    request: HoursHistoryRequest
    window_start: date
    window_kind: Literal["preceding_12_months", "eligible_service_under_12_months"]
    rows: tuple[HistoricalHours, ...]
    total_history_hours: Fraction
    equivalent_weeks: Fraction
    history_hours_per_week: Fraction
    current_hours_per_week: Fraction
    selected_hours_per_week: Fraction
    selected_basis: Literal["history", "commencement", "tie"]


def select_normal_hours(
    rule: NormalHoursRule,
    request: HoursHistoryRequest,
    history: tuple[HistoricalHours, ...],
) -> NormalHoursSelection:
    """Select the greater of an explicitly normalized average and current hours.

    Whole-service history applies only below twelve calendar months and at least
    forty verified continuous weeks. Longer service uses the preceding anniversary
    window with the explicitly selected clamp convention. Observations must be
    preallocated exactly to that window: no clipping or distribution is inferred.
    The supplied rational weeks exposure and its basis remain explicit; choosing
    calendar days/7, payroll weeks or another normalization is upstream review.
    This does not establish variable-part-time/leave eligibility or monetary pay,
    allowance continuation, service-credit rules, accrual or payment dates.
    """
    rule = NormalHoursRule.model_validate(rule.model_dump())
    request = HoursHistoryRequest.model_validate(request.model_dump())
    history = tuple(HistoricalHours.model_validate(h.model_dump()) for h in history)
    when = request.leave_starts_on
    if not rule.effective_from <= when < rule.effective_to:
        msg = "History rule does not cover the leave commencement date"
        raise ValueError(msg)
    source = rule.sources.require_applicable(
        rule.source_id,
        when,
        rule.jurisdiction,
        rule.employer,
        rule.classification,
    )
    if source.sha256 != rule.source_sha256:
        msg = "History rule hash differs from the held source edition"
        raise ValueError(msg)
    if source.retrieved_at is None or source.retrieved_at.date() > rule.as_known_on:
        msg = "History source retrieval is after the declared knowledge date"
        raise ValueError(msg)
    if when - request.continuous_service_from < timedelta(
        weeks=rule.minimum_service_weeks,
    ):
        msg = "Verified continuous service is shorter than the selected rule requires"
        raise ValueError(msg)
    prior_year = when.year - 1
    anniversary = date(
        prior_year,
        when.month,
        min(when.day, monthrange(prior_year, when.month)[1]),
    )
    start = max(anniversary, request.continuous_service_from)
    kind: Literal["preceding_12_months", "eligible_service_under_12_months"] = (
        "eligible_service_under_12_months"
        if start > anniversary
        else "preceding_12_months"
    )
    if len({row.history_id for row in history}) != len(history):
        msg = "Duplicate history identity"
        raise ValueError(msg)
    ordered = tuple(sorted(history, key=lambda h: h.starts_on))
    cursor = start
    for row in ordered:
        if row.starts_on != cursor or row.ends_on > when:
            msg = "History must cover the exact window without gaps or overlaps"
            raise ValueError(msg)
        cursor = row.ends_on
    if cursor != when:
        msg = "Complete history must cover through leave commencement"
        raise ValueError(msg)
    total = sum((Fraction(row.hours) for row in ordered), Fraction(0))
    exposure = Fraction(
        request.equivalent_weeks_numerator,
        request.equivalent_weeks_denominator,
    )
    average = total / exposure
    current = Fraction(request.current_hours_per_week)
    selected: Literal["history", "commencement", "tie"] = (
        "history"
        if average > current
        else "commencement"
        if current > average
        else "tie"
    )
    return NormalHoursSelection(
        "max_history_or_commencement_hours_v1",
        rule,
        request,
        start,
        kind,
        ordered,
        total,
        exposure,
        average,
        current,
        max(average, current),
        selected,
    )
