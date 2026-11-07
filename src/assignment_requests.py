# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Typed scenario requests delegate to the qualified assignment cost functions."""

from datetime import UTC, datetime
from typing import Annotated, Literal
lazy from decimal import Decimal

from pydantic import Field, TypeAdapter, field_validator

from src.assignment_costing import (
    AssignmentCost,
    AssignmentTimeline,
    cost_assignment_activities,
    cost_assignment_snapshot,
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
