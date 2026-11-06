# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Exercise the installed-style v2 CLI with synthetic inputs and safe output."""

from datetime import UTC, datetime
from decimal import Decimal
lazy from pathlib import Path

import pytest

from src.conditions import ConditionRelease, ConditionSnapshotResult
from src.conditions_cli import main
from src.costing import Activity
from src.source_registry import SourceRegistry
from tests.checks import assert_that
from tests.test_conditions import condition
from tests.test_roster_costing import release
from tests.test_source_registry import source


def test_condition_activity_cli_writes_result_without_overwriting(
    tmp_path: Path,
) -> None:
    """JSON input and output retain release identity, amounts and source references."""
    release = ConditionRelease(
        release_id="cli-v2",
        jurisdiction="QLD",
        employer="Synthetic employer",
        classification="Synthetic grade",
        sources=SourceRegistry(records=(source(),)),
        conditions=(
            condition("salary", "salary", "100000", "AUD/year"),
            condition("hours", "paid_hours", "2000", "hours/year"),
        ),
    )
    activity = Activity(
        activity_id="shift",
        resource_id="staff",
        starts_at=datetime(2026, 6, 1, tzinfo=UTC),
        ends_at=datetime(2026, 6, 1, 1, tzinfo=UTC),
        resources=Decimal(1),
    )
    release_path = tmp_path / "release.json"
    activity_path = tmp_path / "activity.json"
    output = tmp_path / "result.json"
    release_path.write_text(release.model_dump_json(), encoding="utf-8")
    activity_path.write_text(activity.model_dump_json(), encoding="utf-8")
    args = [
        "--release",
        str(release_path),
        "--activity",
        str(activity_path),
        "--timezone",
        "UTC",
        "--output",
        str(output),
    ]
    assert_that(main(args) == 0)
    assert_that('"total":"50"' in output.read_text(encoding="utf-8"))
    with pytest.raises(FileExistsError):
        main(args)


def test_snapshot_cli_preserves_exact_total_and_rejects_invalid_mode(
    tmp_path: Path,
) -> None:
    """Snapshot JSON reaches the shared cost function and retains its lineage."""
    release_path = tmp_path / "release.json"
    snapshot_path = tmp_path / "snapshot.json"
    output = tmp_path / "snapshot-result.json"
    release_path.write_text(release().model_dump_json(), encoding="utf-8")
    snapshot_path.write_text('{"as_of":"2026-06-01","hours":"2"}', encoding="utf-8")
    args = [
        "--release",
        str(release_path),
        "--snapshot",
        str(snapshot_path),
        "--output",
        str(output),
    ]
    assert_that(main(args) == 0)

    result = ConditionSnapshotResult.model_validate_json(output.read_bytes())
    assert_that(result.total == Decimal(100))
    assert_that(result.exact_total_numerator == Decimal(100))
    assert_that(result.conditions != ())
    with pytest.raises(FileExistsError):
        main(args)
    with pytest.raises(SystemExit):
        main([*args, "--timezone", "UTC"])
    with pytest.raises(SystemExit):
        main([*args, "--activity", "unused.json"])
