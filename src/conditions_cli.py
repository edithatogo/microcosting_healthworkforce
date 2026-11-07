# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Run explicit single-release or assignment-path costing from JSON."""

import argparse
from pathlib import Path
lazy from datetime import date

from pydantic import TypeAdapter

from src.assignment_costing import AssignmentCost, AssignmentTimeline
from src.assignment_requests import AssignmentRequest, run_assignment_request
from src.conditions import (
    ConditionRelease,
    SnapshotQuantity,
    cost_condition_activity,
    cost_condition_snapshot,
)
from src.costing import Activity


class SnapshotRequest(SnapshotQuantity):
    """Explicit nominal paid hours and valuation date for a snapshot."""

    as_of: date


def main(argv: list[str] | None = None) -> int:
    """Validate both inputs, then create a new output without overwriting files."""
    parser = argparse.ArgumentParser(description=__doc__)
    sources = parser.add_mutually_exclusive_group(required=True)
    sources.add_argument("--release", type=Path)
    sources.add_argument("--timeline", type=Path)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--activity", type=Path)
    inputs.add_argument("--snapshot", type=Path)
    inputs.add_argument("--assignment-request", type=Path)
    parser.add_argument("--timezone")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.timeline is not None:
        if args.assignment_request is None or args.timezone is not None:
            parser.error("--timeline requires --assignment-request and state timezones")
        timeline = AssignmentTimeline.model_validate_json(args.timeline.read_bytes())
        request = TypeAdapter(AssignmentRequest).validate_json(
            args.assignment_request.read_bytes(),
        )
        assignment = run_assignment_request(timeline, request)
        encoded = TypeAdapter(AssignmentCost).dump_json(assignment).decode("utf-8")
        with args.output.open("x", encoding="utf-8") as output:
            output.write(encoded + "\n")
        return 0
    if args.assignment_request is not None:
        parser.error("--assignment-request requires --timeline")
    if args.activity is not None and args.timezone is None:
        parser.error("--activity requires --timezone")
    if args.snapshot is not None and args.timezone is not None:
        parser.error("--timezone applies only to --activity")
    release = ConditionRelease.model_validate_json(args.release.read_bytes())
    if args.snapshot is not None:
        request = SnapshotRequest.model_validate_json(args.snapshot.read_bytes())
        result = cost_condition_snapshot(release, request.as_of, request.hours)
    elif args.activity is not None and args.timezone is not None:
        activity = Activity.model_validate_json(args.activity.read_bytes())
        result = cost_condition_activity(release, activity, args.timezone)
    else:
        parser.error("An activity and timezone or a snapshot is required")
    with args.output.open("x", encoding="utf-8") as output:
        output.write(result.model_dump_json())
        output.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
