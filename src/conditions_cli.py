# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Run explicit single-release or assignment-path costing from JSON."""

import argparse
from pathlib import Path
lazy from datetime import date

from pydantic import TypeAdapter

from src.assignment_costing import AssignmentCost, AssignmentTimeline
from src.assignment_requests import (
    AssignmentActivitiesRequest,
    AssignmentCostWithReimbursements,
    AssignmentRequest,
    AssignmentScenarioComparison,
    compare_assignment_requests,
    cost_assignment_with_reimbursements,
    run_assignment_request,
)
from src.capacity_costing import CapacityScenarioInputs, capacity_scenario
from src.conditions import (
    ConditionRelease,
    SnapshotQuantity,
    WorkbookConditionOrigin,
    cost_condition_activity,
    cost_condition_snapshot,
)
from src.costing import Activity
from src.roster_costing import OvertimeRule, PayPeriod, cost_overtime_period
from src.unit_quotes import QuoteModel
lazy from src.reimbursement import ReimbursementPeriod


class AssignmentReimbursementRequest(QuoteModel):
    """Reviewed claim period explicitly bound to the assignment subject."""

    reviewed_subject_id: str
    period: ReimbursementPeriod


class RosterRequest(QuoteModel):
    """Explicit roster history and overtime rule for a single worker."""

    period: PayPeriod
    rule: OvertimeRule
    activities: tuple[Activity, ...]
    timezone: str


class SnapshotRequest(SnapshotQuantity):
    """Explicit nominal paid hours and valuation date for a snapshot."""

    as_of: date


class CapacityRequest(CapacityScenarioInputs):
    """Explicit annual capacity assumptions and valuation date."""

    as_of: date


def _load_release(release_path: Path, origin_path: Path | None) -> ConditionRelease:
    """Bind an explicit origin mapping before accepting the release for costing."""
    release = ConditionRelease.model_validate_json(release_path.read_bytes())
    if origin_path is not None:
        origins = TypeAdapter(dict[str, WorkbookConditionOrigin]).validate_json(
            origin_path.read_bytes(),
        )
        if not origins.keys() <= {item.condition_id for item in release.conditions}:
            msg = "Workbook origins reference unknown condition IDs"
            raise ValueError(msg)
        for item in release.conditions:
            origin = origins.get(item.condition_id)
            if origin is not None and item.workbook_origin not in (None, origin):
                msg = "Workbook origin conflicts with existing release evidence"
                raise ValueError(msg)
        updated = release.model_copy(
            update={
                "conditions": tuple(
                    item.model_copy(
                        update={
                            "workbook_origin": origins.get(
                                item.condition_id,
                                item.workbook_origin,
                            ),
                        },
                    )
                    for item in release.conditions
                ),
            },
        )
        release = ConditionRelease.model_validate(updated.model_dump())

    return release


def _assignment_output(
    timeline: AssignmentTimeline,
    request: AssignmentRequest,
    comparison_path: Path | None,
    alternative_path: Path | None,
    reimbursement_path: Path | None,
) -> str:
    if reimbursement_path is not None:
        if not isinstance(request, AssignmentActivitiesRequest):
            msg = "Reimbursements require an assignment activity request"
            raise ValueError(msg)
        reviewed = AssignmentReimbursementRequest.model_validate_json(
            reimbursement_path.read_bytes(),
        )
        combined = cost_assignment_with_reimbursements(
            timeline,
            request,
            reviewed.period,
            reviewed_subject_id=reviewed.reviewed_subject_id,
        )
        return (
            TypeAdapter(AssignmentCostWithReimbursements).dump_json(combined).decode()
        )
    if comparison_path is None:
        result = run_assignment_request(timeline, request)
        return TypeAdapter(AssignmentCost).dump_json(result).decode("utf-8")
    alternative = TypeAdapter(AssignmentRequest).validate_json(
        comparison_path.read_bytes(),
    )
    alternative_timeline = (
        timeline
        if alternative_path is None
        else AssignmentTimeline.model_validate_json(alternative_path.read_bytes())
    )
    comparison = compare_assignment_requests(
        timeline,
        request,
        alternative_timeline,
        alternative,
    )
    return (
        TypeAdapter(AssignmentScenarioComparison).dump_json(comparison).decode("utf-8")
    )


def _validate_comparison_options(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> None:
    if args.reimbursements is not None and (
        args.timeline is None or args.compare_assignment_request is not None
    ):
        parser.error(
            "--reimbursements requires --timeline and a single assignment request",
        )
    if args.compare_assignment_request is not None and args.timeline is None:
        parser.error("--compare-assignment-request requires --timeline")
    if (
        args.alternative_timeline is not None
        and args.compare_assignment_request is None
    ):
        parser.error("--alternative-timeline requires --compare-assignment-request")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sources = parser.add_mutually_exclusive_group(required=True)
    sources.add_argument("--release", type=Path)
    sources.add_argument("--timeline", type=Path)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--activity", type=Path)
    inputs.add_argument("--roster", type=Path)
    inputs.add_argument("--snapshot", type=Path)
    inputs.add_argument("--capacity", type=Path)
    inputs.add_argument("--assignment-request", type=Path)
    parser.add_argument("--compare-assignment-request", type=Path)
    parser.add_argument("--alternative-timeline", type=Path)
    parser.add_argument("--reimbursements", type=Path)
    parser.add_argument("--workbook-origins", type=Path)
    parser.add_argument("--timezone")
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Validate both inputs, then create a new output without overwriting files."""
    parser = _parser()
    args = parser.parse_args(argv)
    _validate_comparison_options(parser, args)
    if args.timeline is not None:
        if (
            args.assignment_request is None
            or args.timezone is not None
            or args.workbook_origins is not None
        ):
            parser.error("--timeline requires --assignment-request and state timezones")
        timeline = AssignmentTimeline.model_validate_json(args.timeline.read_bytes())
        request = TypeAdapter(AssignmentRequest).validate_json(
            args.assignment_request.read_bytes(),
        )
        encoded = _assignment_output(
            timeline,
            request,
            args.compare_assignment_request,
            args.alternative_timeline,
            args.reimbursements,
        )
        with args.output.open("x", encoding="utf-8") as output:
            output.write(encoded + "\n")
        return 0
    if args.assignment_request is not None:
        parser.error("--assignment-request requires --timeline")
    if args.activity is not None and args.timezone is None:
        parser.error("--activity requires --timezone")
    if args.activity is None and args.timezone is not None:
        parser.error("--timezone applies only to --activity")
    release = _load_release(args.release, args.workbook_origins)
    if args.roster is not None:
        roster = RosterRequest.model_validate_json(args.roster.read_bytes())
        encoded = cost_overtime_period(
            release,
            roster.period,
            roster.rule,
            roster.activities,
            roster.timezone,
        ).model_dump_json()
    elif args.capacity is not None:
        capacity = CapacityRequest.model_validate_json(args.capacity.read_bytes())
        assumptions = CapacityScenarioInputs.model_validate_json(
            capacity.model_dump_json(exclude={"as_of"}),
        )
        encoded = capacity_scenario(
            release,
            capacity.as_of,
            assumptions,
        ).model_dump_json()
    elif args.snapshot is not None:
        request = SnapshotRequest.model_validate_json(args.snapshot.read_bytes())
        encoded = cost_condition_snapshot(
            release,
            request.as_of,
            request.hours,
        ).model_dump_json()
    elif args.activity is not None and args.timezone is not None:
        activity = Activity.model_validate_json(args.activity.read_bytes())
        encoded = cost_condition_activity(
            release,
            activity,
            args.timezone,
        ).model_dump_json()
    else:
        parser.error(
            "An activity and timezone, a snapshot or a capacity request is required",
        )
    with args.output.open("x", encoding="utf-8") as output:
        output.write(encoded)
        output.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
