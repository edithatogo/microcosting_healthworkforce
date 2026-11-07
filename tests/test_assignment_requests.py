# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Explicit assignment requests share pricing and preserve serialized lineage."""

import json
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from src.assignment_costing import (
    AssignmentCost,
    cost_assignment_activities,
    cost_assignment_snapshot,
)
from src.assignment_requests import AssignmentRequest, run_assignment_request
from src.conditions_cli import main
from tests.checks import assert_that
from tests.test_assignment_costing import CHANGE, activity, timeline


def files(tmp_path: Path, mode: str) -> tuple[list[str], Path]:
    """Only fictional assignments and resource quantities enter CLI fixtures."""
    path = tmp_path / "timeline.json"
    request = tmp_path / "request.json"
    output = tmp_path / "result.json"
    path.write_text(timeline().model_dump_json())
    data = (
        {"mode": "snapshot", "when": CHANGE.isoformat(), "hours": "2"}
        if mode == "snapshot"
        else {"mode": "activities", "activities": [activity().model_dump(mode="json")]}
    )
    request.write_text(json.dumps(data))
    return [
        "--timeline",
        str(path),
        "--assignment-request",
        str(request),
        "--output",
        str(output),
    ], output


@pytest.mark.parametrize("mode", ["snapshot", "activities"])
def test_assignment_request_cli_matches_shared_api(tmp_path: Path, mode: str) -> None:
    """Request adapter, CLI and direct functions produce identical full ledgers."""
    args, output = files(tmp_path, mode)
    request = TypeAdapter(AssignmentRequest).validate_json(Path(args[3]).read_bytes())
    expected = (
        cost_assignment_snapshot(timeline(), CHANGE, Decimal(2))
        if mode == "snapshot"
        else cost_assignment_activities(timeline(), (activity(),))
    )
    assert_that(run_assignment_request(timeline(), request) == expected)
    assert_that(main(args) == 0)
    data = json.loads(output.read_text())
    assert_that(data == json.loads(TypeAdapter(AssignmentCost).dump_json(expected)))
    assert_that(data["timeline_sha256"] == expected.timeline_sha256)
    assert_that(Fraction(data["total"]) == expected.total)
    assert_that(
        data["timeline"]["states"][1]["decision_id"] == "fictional-decision-two",
    )
    assert_that(data["rows"][0]["release_sha256"] == expected.rows[0].release_sha256)
    assert_that(data["method_id"] == "declared_assignment_path_v1")
    original = output.read_bytes()
    with pytest.raises(FileExistsError):
        main(args)
    assert_that(output.read_bytes() == original)


@pytest.mark.parametrize(
    "extra",
    [
        ["--release", "unused.json"],
        ["--snapshot", "unused.json"],
        ["--activity", "unused.json"],
        ["--timezone", "UTC"],
    ],
)
def test_assignment_cli_rejects_conflicting_routes(
    tmp_path: Path,
    extra: list[str],
) -> None:
    """Each request has one source route and its own explicit mode/timezone."""
    args, output = files(tmp_path, "snapshot")
    with pytest.raises(SystemExit):
        main([*args, *extra])
    assert_that(not output.exists())


@pytest.mark.parametrize(
    "payload",
    [
        '{"mode":"projection","when":"2026-06-01T12:00:00Z","hours":"2"}',
        '{"mode":"snapshot","when":"2026-06-01T12:00:00","hours":"2"}',
        '{"mode":"snapshot","when":"2026-06-01T12:00:00Z","hours":"NaN"}',
        '{"mode":"activities","activities":[]}',
        '{"mode":"snapshot","when":"2026-06-01T12:00:00Z","hours":"2","default_rate":"50"}',
    ],
)
def test_assignment_cli_rejects_invalid_requests(tmp_path: Path, payload: str) -> None:
    """Unknown modes, naive dates, invalid quantities and legacy defaults fail."""
    args, output = files(tmp_path, "snapshot")
    Path(args[3]).write_text(payload)
    with pytest.raises(ValidationError):
        main(args)
    assert_that(not output.exists())


def test_assignment_adapter_revalidates_unchecked_request_copy(tmp_path: Path) -> None:
    """Unchecked model copies cannot introduce negative nominal quantities."""
    args, _ = files(tmp_path, "snapshot")
    request = TypeAdapter(AssignmentRequest).validate_json(Path(args[3]).read_bytes())
    bad = request.model_copy(update={"hours": Decimal(-1)})
    with pytest.raises(ValueError, match="greater than or equal"):
        run_assignment_request(timeline(), bad)


def test_assignment_request_cannot_be_used_as_single_release(tmp_path: Path) -> None:
    """The explicit assignment route cannot silently fall back to legacy flags."""
    args, output = files(tmp_path, "snapshot")
    args[0] = "--release"
    with pytest.raises(SystemExit):
        main(args)
    assert_that(not output.exists())
