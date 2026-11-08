# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Exercise the installed-style v2 CLI with synthetic inputs and safe output."""

import json
from datetime import UTC, datetime
from decimal import Decimal
from fractions import Fraction
lazy from pathlib import Path

import pytest

from src.capacity_costing import CapacityScenarioResult
from src.condition_history import release_sha256
from src.conditions import ConditionRelease, ConditionSnapshotResult
from src.conditions_cli import RosterRequest, main
from src.costing import Activity
from src.source_registry import SourceRegistry
from tests.checks import assert_that
from tests.test_conditions import condition
from tests.test_roster_costing import period, release, rule
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
    origin_path = tmp_path / "origins.json"
    origin = {
        "workbook_sha256": "b" * 64,
        "sheet": "Synthetic worksheet",
        "coordinate": "V16",
        "applicability": "conflicting",
        "review_evidence": "Synthetic workbook review",
    }
    mapped_args = [*args, "--workbook-origins", str(origin_path)]
    origin_path.write_text(json.dumps({"salary": origin}), encoding="utf-8")
    with pytest.raises(ValueError, match="verified cell applicability"):
        main(mapped_args)
    assert_that(not output.exists())
    origin["applicability"] = "verified"
    origin_path.write_text(json.dumps({"unknown-condition": origin}), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown condition IDs"):
        main(mapped_args)
    assert_that(not output.exists())
    origin_path.write_text(json.dumps({"salary": origin}), encoding="utf-8")
    assert_that(main(mapped_args) == 0)

    result = ConditionSnapshotResult.model_validate_json(output.read_bytes())
    assert_that(result.total == Decimal(100))
    assert_that(result.exact_total_numerator == Decimal(100))
    assert_that(result.conditions != ())
    stored = result.conditions[0]
    assert_that(stored.workbook_origin is not None)
    original = release()
    with_origin = original.model_copy(
        update={"conditions": (stored, *original.conditions[1:])},
    )
    release_path.write_text(with_origin.model_dump_json(), encoding="utf-8")
    origin["coordinate"] = "X16"
    origin_path.write_text(json.dumps({"salary": origin}), encoding="utf-8")
    before = output.read_bytes()
    with pytest.raises(ValueError, match="conflicts with existing release evidence"):
        main(mapped_args)
    assert_that(output.read_bytes() == before)
    with pytest.raises(FileExistsError):
        main(args)
    with pytest.raises(SystemExit):
        main([*args, "--timezone", "UTC"])
    with pytest.raises(SystemExit):
        main([*args, "--activity", "unused.json"])


@pytest.mark.parametrize(
    ("leave_hours", "cover_hours"),
    [("200", "100"), ("601/3", "301/3")],
)
def test_capacity_cli_retains_assumptions_and_exact_total(
    tmp_path: Path,
    leave_hours: str,
    cover_hours: str,
) -> None:
    """Expose separate paid cost, cover and productive hours through JSON."""
    release_path = tmp_path / "release.json"
    request = tmp_path / "capacity.json"
    output = tmp_path / "result.json"
    release_path.write_text(release().model_dump_json(), encoding="utf-8")
    request.write_text(
        f'{{"as_of":"2026-06-01","losses":[{{"loss_id":"leave","hours":"{leave_hours}"}}],'
        f'"cover_hours":"{cover_hours}","cover_hourly_cost":"60",'
        '"losses_disjoint":true}',
        encoding="utf-8",
    )
    args = [
        "--release",
        str(release_path),
        "--capacity",
        str(request),
        "--output",
        str(output),
    ]
    with pytest.raises(SystemExit):
        main([*args, "--timezone", "UTC"])
    assert_that(not output.exists())
    assert_that(main(args) == 0)
    result = CapacityScenarioResult.model_validate_json(output.read_bytes())
    assert_that(result.paid_cost == Decimal(100000))
    cover_cost = Fraction(cover_hours) * 60
    assert_that(Fraction(result.assumptions.cover_hours) == Fraction(cover_hours))
    assert_that(Fraction(result.incremental_cover_cost) == cover_cost)
    productive = Fraction(2000) - Fraction(leave_hours)
    assert_that(
        Fraction(
            result.exact_productive_rate_numerator,
            result.exact_productive_rate_denominator,
        )
        == (100000 + cover_cost) / productive,
    )
    assert_that(Fraction(result.assumptions.losses[0].hours) == Fraction(leave_hours))
    assert_that(
        Fraction(result.exact_total_numerator, result.exact_total_denominator)
        == 100000 + cover_cost,
    )
    assert_that(result.exact_total_denominator == 1)
    assert_that(result.assumptions.losses[0].loss_id == "leave")
    with pytest.raises(FileExistsError):
        main(args)


@pytest.mark.parametrize("as_array", [False, True])
def test_roster_cli_prices_reviewed_overtime(tmp_path: Path, *, as_array: bool) -> None:
    """Run the overtime ledger through the public JSON entry point."""
    release_path = tmp_path / "release.json"
    release_path.write_text(release().model_dump_json())
    roster_path = tmp_path / "roster.json"
    roster = RosterRequest(
        period=period(),
        rule=(rule(),) if as_array else rule(),
        activities=(
            Activity(
                activity_id="shift",
                resource_id="worker",
                allocation_id="allocation",
                starts_at=datetime(2026, 6, 2, 9, tzinfo=UTC),
                ends_at=datetime(2026, 6, 2, 11, tzinfo=UTC),
                resources=Decimal(1),
            ),
        ),
        timezone="UTC",
    )
    roster_path.write_text(roster.model_dump_json())
    output = tmp_path / "output.json"
    assert_that(
        main(
            [
                "--release",
                str(release_path),
                "--roster",
                str(roster_path),
                "--output",
                str(output),
            ],
        )
        == 0,
    )
    result = json.loads(output.read_text())
    assert_that(result["total"] == "125")
    assert_that(result["resource_id"] == "worker")
    assert_that(result["allocation_id"] == "allocation")
    assert_that(result["period"] == roster.period.model_dump(mode="json"))
    assert_that(result["timezone"] == roster.timezone)
    assert_that(result["release_sha256"] == release_sha256(release()))
    assert_that(result["rows"][0]["rule_id"] == "synthetic-overtime")

    rejected_output = tmp_path / "rejected.json"
    bad_rule = rule().model_copy(update={"source_sha256": "b" * 64})
    roster_path.write_text(
        roster.model_copy(update={"rule": bad_rule}).model_dump_json(),
    )
    with pytest.raises(ValueError, match="Overtime rule source hash mismatch"):
        main(
            [
                "--release",
                str(release_path),
                "--roster",
                str(roster_path),
                "--output",
                str(rejected_output),
            ],
        )
    assert_that(not rejected_output.exists())
