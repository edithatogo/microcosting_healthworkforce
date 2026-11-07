# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Typed scenario requests delegate to the qualified assignment cost functions."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal
from zoneinfo import ZoneInfo
lazy from decimal import Decimal
lazy from fractions import Fraction

from pydantic import Field, TypeAdapter, computed_field, field_validator

from src.assignment_costing import (
    AssignmentCost,
    AssignmentTimeline,
    cost_assignment_activities,
    cost_assignment_snapshot,
)
from src.reimbursement import (
    ReimbursementLedger,
    ReimbursementPeriod,
    build_reimbursement_ledger,
)
from src.unit_quotes import QuoteModel
lazy from src.costing import Activity


class AssignmentSnapshotRequest(QuoteModel):
    """Explicit aware snapshot instant and nonnegative nominal paid hours."""

    mode: Literal["snapshot"]
    when: datetime
    hours: Decimal = Field(ge=0, allow_inf_nan=False)

    @field_validator("when")
    @classmethod
    def aware_instant(cls, value: datetime) -> datetime:
        """Require an instant rather than inferring a local wall-clock offset."""
        if value.utcoffset() is None:
            msg = "Assignment snapshot requires a timezone-aware instant"
            raise ValueError(msg)
        return value.astimezone(UTC)


class AssignmentActivitiesRequest(QuoteModel):
    """Explicit dated resource activities; timezone comes from each state."""

    mode: Literal["activities"]
    activities: tuple[Activity, ...] = Field(min_length=1)


type AssignmentRequest = Annotated[
    AssignmentSnapshotRequest | AssignmentActivitiesRequest,
    Field(discriminator="mode"),
]


def run_assignment_request(
    timeline: AssignmentTimeline,
    request: AssignmentRequest,
) -> AssignmentCost:
    """Use the shared cost function for CLI and paired/scenario requests."""
    request = TypeAdapter(AssignmentRequest).validate_python(request.model_dump())
    if isinstance(request, AssignmentSnapshotRequest):
        return cost_assignment_snapshot(timeline, request.when, request.hours)
    return cost_assignment_activities(timeline, request.activities)


@dataclass(frozen=True)
class AssignmentScenarioComparison:
    """Retain the two exact ledgers underlying a deterministic difference."""

    baseline: AssignmentCost
    alternative: AssignmentCost

    @computed_field
    @property
    def difference(self) -> Fraction:
        """Return alternative minus baseline in ledger currency."""
        return self.alternative.total - self.baseline.total


def compare_assignment_requests(
    baseline_timeline: AssignmentTimeline,
    baseline_request: AssignmentRequest,
    alternative_timeline: AssignmentTimeline,
    alternative_request: AssignmentRequest,
) -> AssignmentScenarioComparison:
    """Compare explicit scenarios for one subject using the same costing mode."""
    if (
        baseline_request.mode != alternative_request.mode
        or baseline_timeline.subject_id != alternative_timeline.subject_id
    ):
        msg = "Assignment comparison requires one subject and one costing mode"
        raise ValueError(msg)
    return AssignmentScenarioComparison(
        run_assignment_request(baseline_timeline, baseline_request),
        run_assignment_request(alternative_timeline, alternative_request),
    )


@dataclass(frozen=True)
class AssignmentCostWithReimbursements:
    """Separate nominal assignment cost and reviewed expenses."""

    assignment: AssignmentCost
    reimbursements: ReimbursementLedger

    @computed_field
    @property
    def total(self) -> Fraction:
        """Combine exact costs in the shared currency."""
        return self.assignment.total + self.reimbursements.total


def cost_assignment_with_reimbursements(
    timeline: AssignmentTimeline,
    request: AssignmentActivitiesRequest,
    period: ReimbursementPeriod,
    *,
    reviewed_subject_id: str,
) -> AssignmentCostWithReimbursements:
    """Price the declared activity and claims for the same reviewed subject.

    Use each priced slice's assignment timezone for the reporting dates.
    Claims are separate expenses and may occur outside worked hours.
    """
    if timeline.subject_id != reviewed_subject_id:
        msg = "Reimbursements require the reviewed assignment subject"
        raise ValueError(msg)
    expenses = build_reimbursement_ledger(period)
    assignment = run_assignment_request(timeline, request)
    if expenses.period.currency != assignment.currency:
        msg = "Assignment and reimbursements require the same currency"
        raise ValueError(msg)
    zones = {
        state.state_id: ZoneInfo(state.timezone) for state in assignment.timeline.states
    }
    for row in assignment.rows:
        zone = zones[row.state_id]
        start = row.starts_at.astimezone(zone).date()
        end = (
            start
            if row.ends_at is None
            else (row.ends_at - timedelta(microseconds=1)).astimezone(zone).date()
        )
        if not expenses.period.starts_on <= start <= end < expenses.period.ends_on:
            msg = "Assignment activity falls outside the reimbursement reporting period"
            raise ValueError(msg)
    return AssignmentCostWithReimbursements(assignment, expenses)
