# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Dated paid/unpaid leave exposures, separate from actual cash and accrued leave.

The caller selects a reviewed profile, approved absence, eligibility and calendar/
offset/accrual conventions. Unknown entitlement debits and accrual remain null.
This method does not resolve family/route facts, extensions or keeping-in-touch.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from fractions import Fraction
from hashlib import sha256
from itertools import pairwise
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from src.unit_quotes import QuoteModel
lazy from src.source_registry import SourceRegistry
lazy from src.unit_quotes import NonnegativeQuantity


class PaidLeavePolicy(QuoteModel):
    """A scoped reviewed paid-leave profile; no automatic instrument selection."""

    policy_id: str
    full_pay_weeks: int = Field(gt=0)
    half_pay_available: bool
    advance_available: bool
    paid_accrual_limit_weeks: int | None = Field(ge=0)
    maximum_absence_weeks: int = Field(gt=0)
    entitlement_budget_weeks: int = Field(ge=0)
    source_id: str
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation: str
    effective_from: date
    effective_to: date
    as_known_on: date
    reviewed: bool
    jurisdiction: str
    employer: str
    classification: str
    sources: SourceRegistry

    @model_validator(mode="after")
    def reviewed_profile(self) -> Self:
        """Require review and bounded operative dates."""
        if not self.reviewed or self.effective_to <= self.effective_from:
            msg = "Paid-leave policy requires review and a nonempty date interval"
            raise ValueError(msg)
        return self


class PaidLeaveRequest(QuoteModel):
    """Explicit approved episode with no inferred debit or unpaid-accrual rule."""

    starts_on: date
    approved_ends_on: date
    payment_mode: Literal["full", "half", "advance"]
    advance_payment_on: date | None
    eligibility_verified: bool
    approval_verified: bool
    eligibility_basis: str
    approval_basis: str
    employment_basis: Literal["ongoing", "fixed_term"]
    contract_ends_on: date | None
    calendar_method: Literal["calendar_days_over_seven_v1"]
    calendar_basis: str
    offset_basis: Literal["calendar_absence", "full_pay_equivalent", "unresolved"]
    offset_review_kind: Literal["source_reviewed", "analyst_assumption", "unresolved"]
    offset_rationale: str
    unpaid_accrual_factor: Annotated[NonnegativeQuantity, Field(le=1)] | None
    unpaid_accrual_review_kind: Literal[
        "source_reviewed",
        "analyst_assumption",
        "unresolved",
    ]
    unpaid_accrual_basis: str
    split_on: tuple[date, ...]

    @model_validator(mode="after")
    def approved_episode(self) -> Self:
        """Reject incomplete eligibility, timing and interpretation declarations."""
        if not self.eligibility_verified or not self.approval_verified:
            msg = "Leave requires explicit eligibility and approval verification"
            raise ValueError(msg)
        if self.approved_ends_on <= self.starts_on:
            msg = "Approved leave date interval must be nonempty"
            raise ValueError(msg)
        if (
            self.employment_basis == "fixed_term"
            and (
                self.contract_ends_on is None
                or self.approved_ends_on > self.contract_ends_on
            )
        ) or (self.employment_basis == "ongoing" and self.contract_ends_on is not None):
            msg = "Fixed-term leave requires a covering contract endpoint"
            raise ValueError(msg)
        if self.payment_mode == "advance":
            if (
                self.advance_payment_on is None
                or self.advance_payment_on >= self.starts_on
            ):
                msg = "Advance payment requires an explicit date before leave"
                raise ValueError(msg)
        elif self.advance_payment_on is not None:
            msg = "An advance date is only valid for the advance payment mode"
            raise ValueError(msg)
        if (self.offset_basis == "unresolved") != (
            self.offset_review_kind == "unresolved"
        ):
            msg = "Entitlement offset basis and review kind must agree"
            raise ValueError(msg)
        if (self.unpaid_accrual_factor is None) != (
            self.unpaid_accrual_review_kind == "unresolved"
        ):
            msg = "Unpaid accrual factor and review kind must agree"
            raise ValueError(msg)
        if len(set(self.split_on)) != len(self.split_on) or any(
            not self.starts_on < day < self.approved_ends_on for day in self.split_on
        ):
            msg = "Leave split dates must be unique and strictly inside approved leave"
            raise ValueError(msg)
        return self


@dataclass(frozen=True)
class LeaveExposureRow:
    """Calendar absence, normal-pay-equivalent weeks and accrual eligibility."""

    starts_on: date
    ends_on: date
    kind: Literal["paid", "unpaid"]
    calendar_weeks: Fraction
    pay_factor: Fraction
    salary_equivalent_weeks: Fraction
    accrual_exposure_weeks: Fraction | None


@dataclass(frozen=True)
class AdvanceInstruction:
    """Caller-selected payment timing; no monetary valuation or actual cash claim."""

    payment_on: date
    full_pay_equivalent_weeks: Fraction


@dataclass(frozen=True)
class PaidLeaveSchedule:
    """Separate state axes and their original source/scenario declarations."""

    method_id: str
    policy: PaidLeavePolicy
    policy_sha256: str
    request: PaidLeaveRequest
    rows: tuple[LeaveExposureRow, ...]
    paid_absence_weeks: Fraction
    unpaid_absence_weeks: Fraction
    salary_equivalent_weeks: Fraction
    unused_salary_equivalent_weeks: Fraction
    accrual_exposure_weeks: Fraction | None
    known_accrual_exposure_weeks: Fraction
    paid_entitlement_debit_weeks: Fraction | None
    remaining_debit_budget_weeks: Fraction | None
    remaining_absence_limit_weeks: Fraction
    advance_instruction: AdvanceInstruction | None


def _admit(policy: PaidLeavePolicy, request: PaidLeaveRequest) -> None:
    """Check payment options, operative source scope and knowledge dates."""
    if request.payment_mode == "half" and not policy.half_pay_available:
        msg = "Selected policy does not admit half pay"
        raise ValueError(msg)
    if request.payment_mode == "advance" and not policy.advance_available:
        msg = "Selected policy does not admit advance payment"
        raise ValueError(msg)
    dates = [request.starts_on, request.approved_ends_on - timedelta(days=1)]
    if request.advance_payment_on is not None:
        dates.append(request.advance_payment_on)
    for day in dates:
        if not policy.effective_from <= day < policy.effective_to:
            msg = "Paid-leave policy does not cover the requested date"
            raise ValueError(msg)
        source = policy.sources.require_applicable(
            policy.source_id,
            day,
            policy.jurisdiction,
            policy.employer,
            policy.classification,
        )
        if source.sha256 != policy.source_sha256:
            msg = "Paid-leave source hash differs from the held edition"
            raise ValueError(msg)
        if (
            source.retrieved_at is None
            or source.retrieved_at.date() > policy.as_known_on
        ):
            msg = "Paid-leave source retrieval exceeds the knowledge date"
            raise ValueError(msg)


def build_paid_leave(
    policy: PaidLeavePolicy,
    request: PaidLeaveRequest,
) -> PaidLeaveSchedule:
    """Build a full/half/advance exposure ledger within explicit approved dates.

    Half pay doubles the profile's paid calendar duration at half normal pay.
    Accrual eligibility stops at the independently declared calendar-week cap;
    unknown caps/unpaid factors remain null. Splits include profile/accrual and
    caller-provided boundaries. Approved shortening preserves unused pay exposure;
    the engine never silently truncates at a contract endpoint or invents approval.
    Advance timing is a separate instruction, not additional payment exposure.
    No payroll rounding, valuation date, entitlement interpretation, working-day
    threshold, extension, keeping-in-touch or actual accrued-leave rate is inferred.
    """
    policy = PaidLeavePolicy.model_validate(policy.model_dump())
    request = PaidLeaveRequest.model_validate(dict(request))
    _admit(policy, request)
    total_weeks = Fraction((request.approved_ends_on - request.starts_on).days, 7)
    if total_weeks > policy.maximum_absence_weeks:
        msg = "Approved absence exceeds the selected policy limit"
        raise ValueError(msg)
    half = request.payment_mode == "half"
    paid_end = request.starts_on + timedelta(
        weeks=policy.full_pay_weeks * (2 if half else 1),
    )
    accrual_end = (
        None
        if policy.paid_accrual_limit_weeks is None
        else request.starts_on + timedelta(weeks=policy.paid_accrual_limit_weeks)
    )
    boundaries = {request.starts_on, request.approved_ends_on, *request.split_on}
    for day in (paid_end, accrual_end):
        if day is not None and request.starts_on < day < request.approved_ends_on:
            boundaries.add(day)
    rows: list[LeaveExposureRow] = []
    for start, end in pairwise(sorted(boundaries)):
        weeks = Fraction((end - start).days, 7)
        paid = start < paid_end
        factor = Fraction(1, 2) if half and paid else Fraction(int(paid))
        if paid:
            accrual = (
                None
                if accrual_end is None
                else weeks
                if start < accrual_end
                else Fraction(0)
            )
        else:
            accrual = (
                None
                if request.unpaid_accrual_factor is None
                else weeks * Fraction(request.unpaid_accrual_factor)
            )
        rows.append(
            LeaveExposureRow(
                start,
                end,
                "paid" if paid else "unpaid",
                weeks,
                factor,
                weeks * factor,
                accrual,
            ),
        )
    paid_weeks = sum((r.calendar_weeks for r in rows if r.kind == "paid"), Fraction(0))
    unpaid_weeks = total_weeks - paid_weeks
    pay = sum((r.salary_equivalent_weeks for r in rows), Fraction(0))
    known_accrual = sum(
        (
            r.accrual_exposure_weeks
            for r in rows
            if r.accrual_exposure_weeks is not None
        ),
        Fraction(0),
    )
    accrual_total = (
        known_accrual
        if all(r.accrual_exposure_weeks is not None for r in rows)
        else None
    )
    debit = (
        None
        if request.offset_basis == "unresolved"
        else paid_weeks
        if request.offset_basis == "calendar_absence"
        else pay
    )
    remaining = (
        None
        if debit is None
        else Fraction(policy.entitlement_budget_weeks) - debit - unpaid_weeks
    )
    if remaining is not None and remaining < 0:
        msg = "Planned leave exceeds the explicitly resolved debit budget"
        raise ValueError(msg)
    instruction = (
        None
        if request.advance_payment_on is None
        else AdvanceInstruction(request.advance_payment_on, pay)
    )
    return PaidLeaveSchedule(
        "paid_leave_exposures_v1",
        policy,
        sha256(policy.model_dump_json().encode()).hexdigest(),
        request,
        tuple(rows),
        paid_weeks,
        unpaid_weeks,
        pay,
        Fraction(policy.full_pay_weeks) - pay,
        accrual_total,
        known_accrual,
        debit,
        remaining,
        Fraction(policy.maximum_absence_weeks) - total_weeks,
        instruction,
    )
