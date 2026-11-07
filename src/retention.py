# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Draft anniversary assessment; source/history integration is not release-qualified."""

from dataclasses import dataclass
from datetime import date, timedelta
from fractions import Fraction
from typing import Literal, Self
lazy from decimal import Decimal

from pydantic import Field, model_validator

from src.unit_quotes import (
    QuoteModel,
    QuoteQuantity,
    UnitQuote,
    UnitQuoteRelease,
    UnitQuoteResult,
    price_units,
)

UNPAID_LEAVE_DISQUALIFYING_WEEKS = 4


class RetentionAssessment(QuoteModel):
    """Explicit assessment facts, without inferring unknown service or receipt."""

    assessment_id: str
    resource_id: str
    assessment_on: date
    history_starts_on: date
    history_ends_on: date
    history_complete: bool
    continuous_service_confirmed: bool
    eligible_location_confirmed: bool
    employment_eligible_confirmed: bool
    annual_amount: Decimal = Field(ge=0, allow_inf_nan=False)
    snapshot_fte: Fraction = Field(ge=0, le=1)
    unpaid_leave_weeks: Fraction = Field(ge=0)
    competing_receipt: Literal["received", "not_received", "unknown"]
    input_kind: Literal["observed_case_evidence", "analyst_assumption"]
    basis: str

    @model_validator(mode="after")
    def complete_assessment(self) -> Self:
        """Require the full fixed-anniversary history and a known receipt state."""
        if self.competing_receipt == "unknown":
            msg = "Competing receipt must be known before assessment"
            raise ValueError(msg)
        expected = date(self.assessment_on.year - 1, 2, 6)
        if (
            (self.assessment_on.month, self.assessment_on.day) != (2, 6)
            or not self.history_complete
            or self.history_starts_on != expected
            or self.history_ends_on != self.assessment_on
        ):
            msg = "Require complete history for the fixed anniversary assessment"
            raise ValueError(msg)
        return self


@dataclass(frozen=True)
class RetentionResult:
    """Retain exact arithmetic, input facts and explicit disqualification reasons."""

    assessment: RetentionAssessment
    amount: Fraction
    reasons: tuple[str, ...]
    scenario: bool


def assess_retention(assessment: RetentionAssessment) -> RetentionResult:
    """Draft clause-53 arithmetic over supplied facts, pending source/history binding.

    This does not derive service, identify an instrument, verify receipt evidence,
    implement pharmacy proration or combine accrual with actual cash payments.
    Do not use this draft as an accepted payroll or library release interface.
    """
    assessment = RetentionAssessment.model_validate(dict(assessment))
    reasons: list[str] = []
    for qualifies, reason in (
        (assessment.continuous_service_confirmed, "continuous_service"),
        (assessment.eligible_location_confirmed, "location"),
        (assessment.employment_eligible_confirmed, "employment"),
        (
            assessment.unpaid_leave_weeks < UNPAID_LEAVE_DISQUALIFYING_WEEKS,
            "unpaid_leave_threshold",
        ),
        (assessment.competing_receipt == "not_received", "competing_receipt"),
    ):
        if not qualifies:
            reasons.append(reason)
    amount = (
        Fraction(0)
        if reasons
        else Fraction(assessment.annual_amount) * assessment.snapshot_fte
    )
    return RetentionResult(
        assessment,
        amount,
        tuple(reasons),
        assessment.input_kind == "analyst_assumption",
    )


class RetentionAuthority(QuoteModel):
    """Reviewed clause-53 authority, price selection and exact worker scope."""

    method: Literal["general_clause53", "pharmacy_retention"] = "general_clause53"
    rule_id: str
    source_id: str
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation: str
    reviewed: bool
    effective_from: date
    effective_to: date
    jurisdiction: str
    employer: str
    classification: str
    quote_id: str
    interpretation_kind: Literal["source_reviewed", "analyst_assumption"]


class RetentionEvidence(QuoteModel):
    """Caller-reviewed evidence covering history, snapshot and actual receipt."""

    evidence_id: str
    evidence_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    resource_id: str
    starts_on: date
    through_on: date
    known_on: date
    covered_facts: tuple[str, ...]
    reviewed: bool
    input_kind: Literal["observed_case_evidence", "analyst_assumption"]
    basis: str


def assess_sourced_retention(
    rule: RetentionAuthority,
    release: UnitQuoteRelease,
    assessment: RetentionAssessment,
    evidence: RetentionEvidence,
) -> tuple[RetentionResult, UnitQuoteResult]:
    """Validate provenance before pricing supplied clause-53 facts.

    Evidence assertions are caller reviews, not file inspection or derivation of
    dated history. Pharmacy service proration and cash settlement remain unsupported.
    """
    rule = RetentionAuthority.model_validate(dict(rule))
    release = UnitQuoteRelease.model_validate(release.model_dump())
    assessment = RetentionAssessment.model_validate(dict(assessment))
    evidence = RetentionEvidence.model_validate(dict(evidence))
    if rule.method != "general_clause53":
        msg = "General retention requires the general clause53 method"
        raise ValueError(msg)
    quote = _validate_retention_binding(rule, release, assessment, evidence)
    day = assessment.assessment_on
    result = assess_retention(assessment)
    scenario = (
        result.scenario
        or rule.interpretation_kind == "analyst_assumption"
        or evidence.input_kind == "analyst_assumption"
    )
    result = RetentionResult(assessment, result.amount, result.reasons, scenario)
    priced = price_units(
        release,
        (
            QuoteQuantity(
                quantity_id=assessment.assessment_id,
                quote_id=quote.quote_id,
                unit=quote.unit,
                quantity=Fraction(0) if result.reasons else assessment.snapshot_fte,
                valued_on=day,
                quantity_kind="analyst_assumption" if scenario else "observed_use",
                basis=assessment.basis,
            ),
        ),
    )
    return result, priced


def _validate_retention_binding(
    rule: RetentionAuthority,
    release: UnitQuoteRelease,
    assessment: RetentionAssessment,
    evidence: RetentionEvidence,
) -> UnitQuote:
    """Shared source/evidence validation without imposing a service formula."""
    day = assessment.assessment_on
    if (
        not rule.reviewed
        or not rule.effective_from <= day < rule.effective_to
        or (rule.jurisdiction, rule.employer, rule.classification)
        != (release.jurisdiction, release.employer, release.classification)
    ):
        msg = "Retention authority requires reviewed matching scope and dates"
        raise ValueError(msg)
    source = release.sources.require_applicable(
        rule.source_id,
        day,
        rule.jurisdiction,
        rule.employer,
        rule.classification,
    )
    if (
        source.sha256 != rule.source_sha256
        or source.retrieved_at is None
        or source.retrieved_at.date() > release.as_known_on
    ):
        msg = "Retention authority requires matching known source hash"
        raise ValueError(msg)
    required = {
        "service",
        "location",
        "employment",
        "snapshot_fte",
        "unpaid_leave",
        "receipt",
    }
    if (
        not evidence.reviewed
        or evidence.resource_id != assessment.resource_id
        or evidence.starts_on > assessment.history_starts_on
        or evidence.through_on < day
        or evidence.known_on > release.as_known_on
        or (evidence.input_kind == "observed_case_evidence" and evidence.known_on < day)
        or set(evidence.covered_facts) != required
        or len(evidence.covered_facts) != len(required)
    ):
        msg = "Retention evidence must cover complete history, snapshot and receipt"
        raise ValueError(msg)
    quote = next((q for q in release.quotes if q.quote_id == rule.quote_id), None)
    if (
        quote is None
        or quote.unit != "anniversary_payment"
        or not quote.starts_on <= day < quote.ends_on
        or quote.amount != assessment.annual_amount
    ):
        msg = "Retention anniversary quote must match amount, unit and assessment date"
        raise ValueError(msg)
    return quote


class RetentionHistorySegment(QuoteModel):
    """Dated reviewed service facts with explicitly measured source-unit absence."""

    segment_id: str
    resource_id: str
    starts_on: date
    ends_on: date
    employed: bool
    qualifying_location: bool
    unpaid_leave_weeks: Fraction = Field(ge=0)
    evidence_id: str
    evidence_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    known_on: date
    measurement_basis: str
    input_kind: Literal["observed_case_evidence", "analyst_assumption"]

    @model_validator(mode="after")
    def positive_interval(self) -> Self:
        """Reject empty service intervals without inventing absence conversions."""
        if self.ends_on <= self.starts_on:
            msg = "Retention history segment must have positive duration"
            raise ValueError(msg)
        return self


def assessment_from_history(
    snapshot: RetentionAssessment,
    history: tuple[RetentionHistorySegment, ...],
) -> RetentionAssessment:
    """Derive prior-year continuity and absence from complete dated records.

    Snapshot employment/location and FTE remain independent anniversary facts.
    Week quantities are supplied measurements with an explicit basis: no calendar
    day/workday conversion or pharmacy service fraction is inferred.
    """
    snapshot = RetentionAssessment.model_validate(dict(snapshot))
    history = tuple(RetentionHistorySegment.model_validate(dict(s)) for s in history)
    if not history or len({s.segment_id for s in history}) != len(history):
        msg = "Require nonempty uniquely identified retention history"
        raise ValueError(msg)
    ordered = sorted(history, key=lambda s: s.starts_on)
    cursor = snapshot.history_starts_on
    for segment in ordered:
        if (
            segment.resource_id != snapshot.resource_id
            or segment.starts_on != cursor
            or segment.ends_on > snapshot.history_ends_on
        ):
            msg = "Retention history must cover one resource without gaps or overlaps"
            raise ValueError(msg)
        cursor = segment.ends_on
    if cursor != snapshot.history_ends_on:
        msg = "Retention history must cover the complete assessment year"
        raise ValueError(msg)
    values = dict(snapshot) | {
        "continuous_service_confirmed": all(s.employed for s in ordered),
        "eligible_location_confirmed": (
            snapshot.eligible_location_confirmed
            and all(s.qualifying_location for s in ordered)
        ),
        "unpaid_leave_weeks": sum(
            (s.unpaid_leave_weeks for s in ordered),
            Fraction(0),
        ),
        "input_kind": (
            "analyst_assumption"
            if snapshot.input_kind == "analyst_assumption"
            or any(s.input_kind == "analyst_assumption" for s in ordered)
            else "observed_case_evidence"
        ),
    }
    return RetentionAssessment.model_validate(values)


@dataclass(frozen=True)
class RetentionHistoryResult:
    """Retain dated input provenance, derived facts and exact scoped prices."""

    authority: RetentionAuthority
    evidence: RetentionEvidence
    history: tuple[RetentionHistorySegment, ...]
    derived_assessment: RetentionAssessment
    assessment_result: RetentionResult
    prices: UnitQuoteResult


def assess_retention_history(
    rule: RetentionAuthority,
    release: UnitQuoteRelease,
    snapshot: RetentionAssessment,
    evidence: RetentionEvidence,
    history: tuple[RetentionHistorySegment, ...],
) -> RetentionHistoryResult:
    """Compose complete dated service derivation with source-qualified pricing."""
    rule = RetentionAuthority.model_validate(dict(rule))
    release = UnitQuoteRelease.model_validate(release.model_dump())
    evidence = RetentionEvidence.model_validate(dict(evidence))
    history = tuple(RetentionHistorySegment.model_validate(dict(s)) for s in history)
    for segment in history:
        if segment.known_on > release.as_known_on or (
            segment.input_kind == "observed_case_evidence"
            and segment.known_on < segment.ends_on - timedelta(days=1)
        ):
            msg = (
                "Retention history evidence must cover observation and knowledge dates"
            )
            raise ValueError(msg)
    derived = assessment_from_history(snapshot, history)
    result, prices = assess_sourced_retention(rule, release, derived, evidence)
    return RetentionHistoryResult(
        rule,
        evidence,
        tuple(sorted(history, key=lambda s: s.starts_on)),
        derived,
        result,
        prices,
    )


class PharmacyServicePortion(QuoteModel):
    """Explicit credited service and FTE under a declared allocation convention."""

    portion_id: str
    measured_units: Fraction = Field(gt=0)
    credit_fraction: Fraction = Field(ge=0, le=1)
    contracted_fte: Fraction = Field(ge=0, le=1)
    category: Literal["service", "workers_compensation", "unpaid_leave", "not_employed"]
    basis: str

    @model_validator(mode="after")
    def excluded_credit(self) -> Self:
        """Compensation and nonemployment cannot count toward service credit."""
        if (
            self.category in {"workers_compensation", "not_employed"}
            and self.credit_fraction
        ):
            msg = "Excluded pharmacy service must have zero credit"
            raise ValueError(msg)
        return self


class PharmacyRetentionProration(QuoteModel):
    """Reviewed explicit service denominator; no automatic date/unit conversion."""

    assessment_id: str
    annual_amount: Decimal = Field(ge=0, allow_inf_nan=False)
    period_units: Fraction = Field(gt=0)
    unit: str
    portions: tuple[PharmacyServicePortion, ...] = Field(min_length=1)
    allocation_method: Literal["credited_service_weighted_fte_v1"]
    interpretation_kind: Literal["source_reviewed", "analyst_assumption"]
    interpretation_basis: str
    eligibility_confirmed: bool
    history_complete: bool

    @model_validator(mode="after")
    def complete_denominator(self) -> Self:
        """Require complete measured history and a distinct identity per portion."""
        if (
            not self.history_complete
            or len({p.portion_id for p in self.portions}) != len(self.portions)
            or sum((p.measured_units for p in self.portions), Fraction(0))
            != self.period_units
        ):
            msg = "Pharmacy proration requires complete unique denominator coverage"
            raise ValueError(msg)
        return self


def prorate_pharmacy_retention(request: PharmacyRetentionProration) -> Fraction:
    """Draft explicit service/FTE composition, without accepting a worker's policy.

    The allocation convention must be independently reviewed or labelled as an
    assumption, especially for changing FTE/location. Unpaid-leave credit requires
    source-specific threshold review. No fixed year, month or workday is inferred.
    This arithmetic helper does not replace source, receipt or dated evidence binding.
    """
    request = PharmacyRetentionProration.model_validate(
        dict(request)
        | {
            "portions": tuple(
                PharmacyServicePortion.model_validate(dict(p)) for p in request.portions
            ),
        },
    )
    if not request.eligibility_confirmed:
        return Fraction(0)
    weighted = sum(
        (
            p.measured_units * p.credit_fraction * p.contracted_fte
            for p in request.portions
        ),
        Fraction(0),
    )
    return Fraction(request.annual_amount) * weighted / request.period_units


@dataclass(frozen=True)
class PharmacyRetentionResult:
    """Retain source, service allocation, evidence and exact priced entitlement."""

    authority: RetentionAuthority
    evidence: RetentionEvidence
    snapshot: RetentionAssessment
    proration: PharmacyRetentionProration
    amount: Fraction
    scenario: bool
    prices: UnitQuoteResult


def assess_pharmacy_retention(
    rule: RetentionAuthority,
    release: UnitQuoteRelease,
    snapshot: RetentionAssessment,
    evidence: RetentionEvidence,
    proration: PharmacyRetentionProration,
) -> PharmacyRetentionResult:
    """Bind explicit pharmacy service allocation to authority and known receipt.

    The general four-week disqualification and snapshot-FTE multiplication are
    not applied. The proration already contains its reviewed service/FTE factors.
    Actual dated measurement and source interpretation remain caller evidence.
    """
    rule = RetentionAuthority.model_validate(dict(rule))
    release = UnitQuoteRelease.model_validate(release.model_dump())
    snapshot = RetentionAssessment.model_validate(dict(snapshot))
    evidence = RetentionEvidence.model_validate(dict(evidence))
    proration = PharmacyRetentionProration.model_validate(
        dict(proration)
        | {
            "portions": tuple(
                PharmacyServicePortion.model_validate(dict(p))
                for p in proration.portions
            ),
        },
    )
    if rule.method != "pharmacy_retention":
        msg = "Pharmacy retention requires an explicit pharmacy method"
        raise ValueError(msg)
    quote = _validate_retention_binding(rule, release, snapshot, evidence)
    if (
        proration.assessment_id != snapshot.assessment_id
        or proration.annual_amount != snapshot.annual_amount
    ):
        msg = "Pharmacy proration must match the assessment identity and annual amount"
        raise ValueError(msg)
    amount = prorate_pharmacy_retention(proration)
    if (
        not snapshot.employment_eligible_confirmed
        or not snapshot.eligible_location_confirmed
    ):
        amount = Fraction(0)
    if snapshot.competing_receipt == "received":
        msg = "Existing competing receipt requires separate settlement review"
        raise ValueError(msg)
    scenario = (
        snapshot.input_kind == "analyst_assumption"
        or evidence.input_kind == "analyst_assumption"
        or rule.interpretation_kind == "analyst_assumption"
        or proration.interpretation_kind == "analyst_assumption"
    )
    quantity = amount / Fraction(quote.amount) if quote.amount else Fraction(0)
    prices = price_units(
        release,
        (
            QuoteQuantity(
                quantity_id=snapshot.assessment_id,
                quote_id=quote.quote_id,
                unit=quote.unit,
                quantity=quantity,
                valued_on=snapshot.assessment_on,
                quantity_kind="analyst_assumption" if scenario else "observed_use",
                basis=proration.interpretation_basis,
            ),
        ),
    )
    return PharmacyRetentionResult(
        rule,
        evidence,
        snapshot,
        proration,
        amount,
        scenario,
        prices,
    )
