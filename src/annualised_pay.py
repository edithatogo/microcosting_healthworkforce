# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Exact complete-window wage comparisons and separate reviewed settlement periods."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from fractions import Fraction
from hashlib import sha256
from itertools import pairwise
from typing import Literal, Self
from zoneinfo import ZoneInfo
lazy from datetime import date

from pydantic import Field, field_validator, model_validator

from src.pay_period_effective import PeriodCalendar
from src.unit_quotes import QuoteModel
lazy from src.source_registry import SourceRegistry
lazy from src.unit_quotes import NonnegativeQuantity


class AnnualisedPayRule(QuoteModel):
    """Explicit source scope, period count and two complete wage-component bases."""

    rule_id: str
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    comparison_periods: int = Field(gt=0)
    period_unit: Literal["fortnight"]
    annualised_components: tuple[str, ...] = Field(min_length=1)
    agreement_components: tuple[str, ...] = Field(min_length=1)
    component_basis: str
    local_timezone: str
    as_known_on: date
    source_id: str
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation: str
    reviewed: bool
    effective_from: date
    effective_to: date
    jurisdiction: str
    employer: str
    classification: str
    sources: SourceRegistry

    @model_validator(mode="after")
    def valid_rule(self) -> Self:
        """Require review, bounded dates and unique nonblank components per side."""
        ZoneInfo(self.local_timezone)
        if not self.reviewed or self.effective_to <= self.effective_from:
            msg = "Wage comparison requires reviewed nonempty rule coverage"
            raise ValueError(msg)
        for names in (self.annualised_components, self.agreement_components):
            if len(set(names)) != len(names) or any(not n.strip() for n in names):
                msg = "Wage component names must be unique and nonblank per side"
                raise ValueError(msg)
        return self


class ReviewSettlement(QuoteModel):
    """Explicit completed review and selection convention, not actual cash paid."""

    completed_at: datetime
    calendar: PeriodCalendar
    boundary_method: Literal["first_period_start_strictly_after_review"]
    convention_kind: Literal["source_reviewed", "analyst_assumption"]
    convention_basis: str


class AnnualisedPayRequest(QuoteModel):
    """One eligible case with complete comparison history and review status."""

    case_id: str
    calendar: PeriodCalendar
    eligibility_verified: bool
    eligibility_basis: str
    earnings_complete: bool
    review_requested: bool
    settlement: ReviewSettlement | None

    @model_validator(mode="after")
    def complete_request(self) -> Self:
        """Unknown eligibility/history and unrequested reviews cannot be filled in."""
        if not self.eligibility_verified or not self.earnings_complete:
            msg = "Verified eligibility and complete relevant wages are required"
            raise ValueError(msg)
        if self.settlement is not None and not self.review_requested:
            msg = "Completed settlement review requires an explicit review request"
            raise ValueError(msg)
        return self


class WagePeriodEvidence(QuoteModel):
    """Complete wage amounts with distinct paid/counterfactual/scenario evidence."""

    period_id: str
    starts_at: datetime
    ends_at: datetime
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    annualised: dict[str, NonnegativeQuantity]
    agreement: dict[str, NonnegativeQuantity]
    annualised_kind: Literal["observed_pay", "analyst_assumption"]
    agreement_kind: Literal["reviewed_counterfactual", "analyst_assumption"]
    annualised_evidence_id: str
    annualised_evidence_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    agreement_evidence_id: str
    agreement_evidence_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    annualised_known_on: date
    agreement_known_on: date
    basis: str

    @field_validator("starts_at", "ends_at")
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        """Normalize economic period instants without treating wall time as elapsed."""
        return _utc(value)


def _utc(value: datetime) -> datetime:
    if value.utcoffset() is None:
        msg = "Wage comparison times must be timezone aware"
        raise ValueError(msg)
    return value.astimezone(UTC)


def _fortnights(calendar: PeriodCalendar, zone: ZoneInfo) -> None:
    for start, end in pairwise(calendar.boundaries):
        expected = start.astimezone(zone) + timedelta(weeks=2)
        if expected.astimezone(UTC) != end:
            msg = "Calendar requires consecutive local-calendar fortnights"
            raise ValueError(msg)


def _source(rule: AnnualisedPayRule, day: date) -> None:
    if not rule.effective_from <= day < rule.effective_to:
        msg = "Wage rule does not cover the requested date"
        raise ValueError(msg)
    source = rule.sources.require_applicable(
        rule.source_id,
        day,
        rule.jurisdiction,
        rule.employer,
        rule.classification,
    )
    if source.sha256 != rule.source_sha256:
        msg = "Wage comparison source hash mismatch"
        raise ValueError(msg)
    if source.retrieved_at is None or source.retrieved_at.date() > rule.as_known_on:
        msg = "Wage comparison source exceeds the knowledge date"
        raise ValueError(msg)


@dataclass(frozen=True)
class WageComparisonRow:
    """Unchanged input evidence and exact signed difference for one pay period."""

    evidence: WagePeriodEvidence
    annualised_total: Fraction
    agreement_total: Fraction
    net_difference: Fraction


@dataclass(frozen=True)
class AnnualisedPayComparison:
    """One whole-window shortfall, separate from a selected future payment period."""

    method_id: str
    rule: AnnualisedPayRule
    rule_sha256: str
    request: AnnualisedPayRequest
    mode: Literal["scenario", "reviewed_pay_records"]
    rows: tuple[WageComparisonRow, ...]
    annualised_total: Fraction
    agreement_total: Fraction
    shortfall: Fraction
    minimum_total: Fraction
    payment_period: tuple[datetime, datetime] | None


def _review_period(
    rule: AnnualisedPayRule,
    request: AnnualisedPayRequest,
    zone: ZoneInfo,
) -> tuple[datetime, datetime] | None:
    settlement = request.settlement
    if settlement is None:
        return None
    completed = _utc(settlement.completed_at)
    if completed < request.calendar.boundaries[-1]:
        msg = "Review cannot finish before the complete comparison window ends"
        raise ValueError(msg)
    if completed.astimezone(zone).date() > rule.as_known_on:
        msg = "Completed review exceeds the knowledge date"
        raise ValueError(msg)
    _source(rule, completed.astimezone(zone).date())
    calendar = PeriodCalendar.model_validate(settlement.calendar.model_dump())
    _fortnights(calendar, zone)
    if calendar.boundaries[0] > completed:
        msg = "Settlement calendar must include a boundary at or before review"
        raise ValueError(msg)
    for start, end in pairwise(calendar.boundaries):
        if start > completed:
            return start, end
    msg = "Calendar does not cover the next complete settlement pay period"
    raise ValueError(msg)


def _row(
    rule: AnnualisedPayRule,
    evidence: WagePeriodEvidence,
    zone: ZoneInfo,
) -> WageComparisonRow:
    if evidence.currency != rule.currency:
        msg = "Comparison wages must share the rule currency"
        raise ValueError(msg)
    for values, expected in (
        (evidence.annualised, rule.annualised_components),
        (evidence.agreement, rule.agreement_components),
    ):
        if set(values) != set(expected):
            msg = (
                "Every declared wage component must be supplied, including known zeros"
            )
            raise ValueError(msg)
    if (
        max(evidence.annualised_known_on, evidence.agreement_known_on)
        > rule.as_known_on
    ):
        msg = "Wage evidence exceeds the knowledge date"
        raise ValueError(msg)
    last_day = (evidence.ends_at - timedelta(microseconds=1)).astimezone(zone).date()
    if evidence.annualised_kind == "observed_pay" and last_day > rule.as_known_on:
        msg = "Observed pay cannot describe a future comparison period"
        raise ValueError(msg)
    _source(rule, evidence.starts_at.astimezone(zone).date())
    _source(rule, last_day)
    annualised = sum((Fraction(v) for v in evidence.annualised.values()), Fraction(0))
    agreement = sum((Fraction(v) for v in evidence.agreement.values()), Fraction(0))
    return WageComparisonRow(evidence, annualised, agreement, agreement - annualised)


def compare_annualised_pay(
    rule: AnnualisedPayRule,
    request: AnnualisedPayRequest,
    earnings: tuple[WagePeriodEvidence, ...],
) -> AnnualisedPayComparison:
    """Compare complete wage alternatives once after summing the whole window.

    Every component and pay period must be explicitly supplied. Counterfactual
    wage calculations and paid-amount evidence are upstream inputs, not inferred
    from an annualised salary or a roster average. A pending/unrequested review
    leaves payment timing unknown. A completed review uses the declared strict
    next-period convention and calendar; no actual cash posting occurs.
    """
    rule = AnnualisedPayRule.model_validate(rule.model_dump())
    request = AnnualisedPayRequest.model_validate(request.model_dump())
    earnings = tuple(WagePeriodEvidence.model_validate(dict(r)) for r in earnings)
    zone = ZoneInfo(rule.local_timezone)
    _fortnights(request.calendar, zone)
    intervals = tuple(pairwise(request.calendar.boundaries))
    if len(intervals) != rule.comparison_periods:
        msg = "Comparison calendar has the wrong number of pay periods"
        raise ValueError(msg)
    by_interval = {(r.starts_at, r.ends_at): r for r in earnings}
    if (
        len(by_interval) != len(earnings)
        or set(by_interval) != set(intervals)
        or len({r.period_id for r in earnings}) != len(earnings)
    ):
        msg = "Exactly one distinct wage record is required for each comparison period"
        raise ValueError(msg)
    rows = tuple(_row(rule, by_interval[p], zone) for p in intervals)
    annualised = sum((r.annualised_total for r in rows), Fraction(0))
    agreement = sum((r.agreement_total for r in rows), Fraction(0))
    shortfall = max(Fraction(0), agreement - annualised)
    payment_period = _review_period(rule, request, zone)
    observed = all(
        r.evidence.annualised_kind == "observed_pay"
        and r.evidence.agreement_kind == "reviewed_counterfactual"
        for r in rows
    ) and (
        request.settlement is None
        or request.settlement.convention_kind == "source_reviewed"
    )
    return AnnualisedPayComparison(
        "complete_window_annualised_comparison_v1",
        rule,
        sha256(rule.model_dump_json().encode()).hexdigest(),
        request,
        "reviewed_pay_records" if observed else "scenario",
        rows,
        annualised,
        agreement,
        shortfall,
        annualised + shortfall,
        payment_period if shortfall else None,
    )
