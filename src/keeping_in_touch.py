# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Explicit KIT eligibility/day-count state, work quantities and extension decisions.

The rule author selects timing/count interpretations. Actual work hours, counted
local days and approved extension quantities are separate; no schedule is mutated.
"""

from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from typing import Annotated, Literal, Self
lazy from datetime import date

from pydantic import Field, model_validator

from src.unit_quotes import QuoteModel
lazy from src.source_registry import SourceRegistry
lazy from src.unit_quotes import NonnegativeQuantity


class KeepingInTouchRule(QuoteModel):
    """Scoped reviewed source and explicit timing/count interpretation."""

    rule_id: str
    employee_wait_days: int = Field(ge=0)
    employer_wait_days: int = Field(ge=0)
    day_limit: int = Field(gt=0)
    count_scope: Literal["per_period", "whole_episode"]
    day_count_method: Literal["unique_calendar_day"]
    interpretation_kind: Literal["source_reviewed", "analyst_assumption"]
    interpretation_basis: str
    source_id: str
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation: str
    reviewed: bool
    effective_from: date
    effective_to: date
    as_known_on: date
    jurisdiction: str
    employer: str
    classification: str
    sources: SourceRegistry

    @model_validator(mode="after")
    def valid_rule(self) -> Self:
        """Require review, bounded dates and consistent request waiting times."""
        if (
            not self.reviewed
            or self.effective_to <= self.effective_from
            or self.employer_wait_days < self.employee_wait_days
        ):
            msg = "KIT rule requires review, valid dates and consistent timing"
            raise ValueError(msg)
        return self


class KITWindow(QuoteModel):
    """A half-open local-calendar approved time interval."""

    starts_on: date
    ends_on: date

    @model_validator(mode="after")
    def nonempty(self) -> Self:
        """Reject empty or reversed windows."""
        if self.ends_on <= self.starts_on:
            msg = "KIT window must be nonempty"
            raise ValueError(msg)
        return self


class KITPeriod(KITWindow):
    """Initial leave or one immediately following approved unpaid extension."""

    period_id: str
    kind: Literal["initial", "extension"]
    approval_verified: bool
    approval_basis: str

    @model_validator(mode="after")
    def approved(self) -> Self:
        """Require an explicit approval assertion; infer no extension right."""
        if not self.approval_verified:
            msg = "KIT period requires verified approval"
            raise ValueError(msg)
        return self


class KITLeaveInterval(KITWindow):
    """Caller-qualified paid/unpaid classification, not inferred from work."""

    interval_id: str
    period_id: str
    kind: Literal["paid", "unpaid"]


def _validate_periods(periods: tuple[KITPeriod, ...]) -> None:
    ordered = sorted(periods, key=lambda p: p.starts_on)
    if len({p.period_id for p in ordered}) != len(ordered):
        msg = "Duplicate KIT period identity"
        raise ValueError(msg)
    if ordered[0].kind != "initial" or (
        len(ordered) > 1 and ordered[1].kind != "extension"
    ):
        msg = "KIT history requires one initial period and optional extension"
        raise ValueError(msg)
    if len(ordered) > 1 and ordered[0].ends_on != ordered[1].starts_on:
        msg = "KIT extension must be contiguous with initial leave"
        raise ValueError(msg)


def _validate_intervals(
    periods: tuple[KITPeriod, ...],
    intervals: tuple[KITLeaveInterval, ...],
) -> None:
    ids = {p.period_id for p in periods}
    if len({r.interval_id for r in intervals}) != len(intervals) or any(
        r.period_id not in ids for r in intervals
    ):
        msg = "Duplicate or unknown KIT leave interval identity"
        raise ValueError(msg)
    for period in periods:
        rows = sorted(
            (r for r in intervals if r.period_id == period.period_id),
            key=lambda r: r.starts_on,
        )
        cursor = period.starts_on
        for row in rows:
            if row.starts_on != cursor or row.ends_on > period.ends_on:
                msg = "KIT leave intervals must cover without gaps or overlaps"
                raise ValueError(msg)
            if period.kind == "extension" and row.kind != "unpaid":
                msg = "KIT extension period must be unpaid"
                raise ValueError(msg)
            cursor = row.ends_on
        if cursor != period.ends_on:
            msg = "KIT leave intervals must cover each approved period"
            raise ValueError(msg)


class KITContext(QuoteModel):
    """Complete relevant history/scenario with explicit approved chronology."""

    scenario_id: str
    assessed_on: date
    birth_or_placement_on: date
    history_complete: bool
    eligibility_verified: bool
    eligibility_basis: str
    local_day_basis: str
    periods: tuple[KITPeriod, ...] = Field(min_length=1, max_length=2)
    leave_intervals: tuple[KITLeaveInterval, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_chronology(self) -> Self:
        """Require complete history and full initial/extension classifications."""
        if not self.history_complete or not self.eligibility_verified:
            msg = "Complete KIT history and verified eligibility are required"
            raise ValueError(msg)
        _validate_periods(self.periods)
        _validate_intervals(self.periods, self.leave_intervals)
        return self


class KITWork(QuoteModel):
    """A positive paid work fragment assigned to an explicit local day/entity."""

    work_id: str
    day: date
    entity_id: str
    requested_by: Literal["employee", "employer"]
    hours: Annotated[NonnegativeQuantity, Field(gt=0)]
    quantity_kind: Literal["observed_use", "analyst_assumption"]
    basis: str
    purpose_verified: bool
    employee_consented: bool
    employer_consented: bool
    paid_work_verified: bool
    external_qualification_verified: bool
    external_qualification_basis: str | None

    @model_validator(mode="after")
    def consent_and_purpose(self) -> Self:
        """Require consent, return purpose and explicitly verified paid work."""
        if not all(
            (
                self.purpose_verified,
                self.employee_consented,
                self.employer_consented,
                self.paid_work_verified,
            ),
        ):
            msg = "KIT work requires consent, return purpose and paid-work verification"
            raise ValueError(msg)
        if self.external_qualification_verified != (
            self.external_qualification_basis is not None
        ):
            msg = "External KIT qualification requires an explicit basis"
            raise ValueError(msg)
        return self


class KITExtension(QuoteModel):
    """One reviewed/unknown primary-employer extension decision per counted day."""

    period_id: str
    day: date
    paid_extension_weeks: Annotated[NonnegativeQuantity, Field(gt=0)] | None
    unit: Literal["calendar_week"]
    review_kind: Literal[
        "source_reviewed",
        "analyst_assumption",
        "unresolved",
        "not_applicable",
    ]
    basis: str

    @model_validator(mode="after")
    def reviewed_quantity(self) -> Self:
        """Keep unknown/non-applicable values null and supplied deltas positive."""
        resolved = self.review_kind in {"source_reviewed", "analyst_assumption"}
        if resolved != (self.paid_extension_weeks is not None):
            msg = "KIT extension quantity and review decision must agree"
            raise ValueError(msg)
        return self


@dataclass(frozen=True)
class KITDayState:
    """One consumed local day, its work fragments and extension decision."""

    period_id: str
    day: date
    count_key: str
    ordinal: int
    leave_kind: str
    work_hours: Fraction
    local_work_hours: Fraction
    work: tuple[KITWork, ...]
    extension: KITExtension
    paid_extension_weeks: Fraction | None


@dataclass(frozen=True)
class KeepingInTouchLedger:
    """Exact count/work/extension state; no automatic absence or cash mutation."""

    method_id: str
    rule: KeepingInTouchRule
    rule_sha256: str
    context: KITContext
    days: tuple[KITDayState, ...]
    count_usage: tuple[tuple[str, int], ...]
    total_work_hours: Fraction
    local_work_hours: Fraction
    paid_extension_weeks: Fraction | None
    known_paid_extension_weeks: Fraction
    unpaid_extension_weeks: Fraction


def _admit(
    rule: KeepingInTouchRule,
    context: KITContext,
    work: tuple[KITWork, ...],
) -> None:
    for day in {context.assessed_on, *(w.day for w in work)}:
        if not rule.effective_from <= day < rule.effective_to:
            msg = "KIT rule does not cover the assessment/work date"
            raise ValueError(msg)
        source = rule.sources.require_applicable(
            rule.source_id,
            day,
            rule.jurisdiction,
            rule.employer,
            rule.classification,
        )
        if source.sha256 != rule.source_sha256:
            msg = "KIT source hash differs from the held edition"
            raise ValueError(msg)
        if source.retrieved_at is None or source.retrieved_at.date() > rule.as_known_on:
            msg = "KIT source retrieval exceeds the knowledge date"
            raise ValueError(msg)


def _work_groups(
    rule: KeepingInTouchRule,
    context: KITContext,
    work: tuple[KITWork, ...],
) -> dict[tuple[str, date], list[KITWork]]:
    if len({w.work_id for w in work}) != len(work):
        msg = "Duplicate work identity"
        raise ValueError(msg)
    groups: dict[tuple[str, date], list[KITWork]] = {}
    for event in work:
        rows = [
            r for r in context.leave_intervals if r.starts_on <= event.day < r.ends_on
        ]
        if len(rows) != 1:
            msg = "KIT work day is outside the approved leave chronology"
            raise ValueError(msg)
        local = event.entity_id == rule.employer
        if not local and not event.external_qualification_verified:
            msg = "Other-entity KIT history requires external qualification"
            raise ValueError(msg)
        wait = (
            rule.employer_wait_days
            if local and event.requested_by == "employer"
            else rule.employee_wait_days
        )
        if (event.day - context.birth_or_placement_on).days < wait:
            msg = "KIT request timing is earlier than the selected rule allows"
            raise ValueError(msg)
        if event.quantity_kind == "observed_use" and event.day > min(
            rule.as_known_on,
            context.assessed_on,
        ):
            msg = "Observed KIT work cannot be after the knowledge date"
            raise ValueError(msg)
        groups.setdefault((rows[0].period_id, event.day), []).append(event)
    return groups


def _extension_value(
    decision: KITExtension,
    leave_kind: str,
    local_hours: Fraction,
) -> Fraction | None:
    if leave_kind != "paid" or local_hours == 0:
        if decision.review_kind != "not_applicable":
            msg = "unpaid or external-only work cannot extend primary paid leave"
            raise ValueError(msg)
        return Fraction(0)
    if decision.review_kind == "not_applicable":
        msg = "Local paid-leave KIT work needs a resolved or unknown extension decision"
        raise ValueError(msg)
    return (
        None
        if decision.paid_extension_weeks is None
        else Fraction(decision.paid_extension_weeks)
    )


def evaluate_kit(
    rule: KeepingInTouchRule,
    context: KITContext,
    work: tuple[KITWork, ...],
    extensions: tuple[KITExtension, ...],
) -> KeepingInTouchLedger:
    """Validate complete KIT history under explicitly selected interpretations.

    Local-day fragments across entities consume one day, retaining exact hours.
    Qualified external records consume capacity without becoming primary-employer
    work or extensions. Initial/extension versus whole-episode caps are explicit.
    Paid extension is supplied once per day or remains unknown; unpaid extension
    is zero. No actual-work quantity is equated with absence extension, no calendar
    end is moved, and no source-specific wage/cash/accrual rule is inferred.
    """
    rule = KeepingInTouchRule.model_validate(rule.model_dump())
    context = KITContext.model_validate(context.model_dump())
    work = tuple(KITWork.model_validate(dict(w)) for w in work)
    extensions = tuple(KITExtension.model_validate(dict(e)) for e in extensions)
    _admit(rule, context, work)
    groups = _work_groups(rule, context, work)
    decisions = {(e.period_id, e.day): e for e in extensions}
    if len(decisions) != len(extensions) or decisions.keys() != groups.keys():
        msg = "Exactly one extension decision is required for each counted day"
        raise ValueError(msg)
    counts: dict[str, int] = {}
    days: list[KITDayState] = []
    for (period_id, day), events in sorted(
        groups.items(),
        key=lambda item: (item[0][1], item[0][0]),
    ):
        key = period_id if rule.count_scope == "per_period" else "whole_episode"
        counts[key] = counts.get(key, 0) + 1
        if counts[key] > rule.day_limit:
            msg = "KIT day limit exceeded in the selected count scope"
            raise ValueError(msg)
        interval = next(
            r for r in context.leave_intervals if r.starts_on <= day < r.ends_on
        )
        ordered = tuple(sorted(events, key=lambda e: e.work_id))
        hours = sum((Fraction(e.hours) for e in ordered), Fraction(0))
        local = sum(
            (Fraction(e.hours) for e in ordered if e.entity_id == rule.employer),
            Fraction(0),
        )
        decision = decisions[(period_id, day)]
        extension = _extension_value(decision, interval.kind, local)
        days.append(
            KITDayState(
                period_id,
                day,
                key,
                counts[key],
                interval.kind,
                hours,
                local,
                ordered,
                decision,
                extension,
            ),
        )
    known = sum(
        (d.paid_extension_weeks for d in days if d.paid_extension_weeks is not None),
        Fraction(0),
    )
    total = known if all(d.paid_extension_weeks is not None for d in days) else None
    return KeepingInTouchLedger(
        "kit_day_history_v1",
        rule,
        sha256(rule.model_dump_json().encode()).hexdigest(),
        context,
        tuple(days),
        tuple(sorted(counts.items())),
        sum((d.work_hours for d in days), Fraction(0)),
        sum((d.local_work_hours for d in days), Fraction(0)),
        total,
        known,
        Fraction(0),
    )
