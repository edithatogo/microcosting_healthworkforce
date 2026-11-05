# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Synthetic versioned condition and explicit salary-loading rule contracts."""

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from src.conditions import (
    Condition,
    ConditionRelease,
    cost_condition_activity,
    hourly_components,
)
from src.costing import Activity
from src.source_registry import SourceRegistry
from tests.checks import assert_that
from tests.test_source_registry import source


def condition(identity: str, kind: str, value: str, unit: str) -> Condition:
    """Construct an explicitly reviewed synthetic condition."""
    return Condition.model_validate(
        {
            "condition_id": identity,
            "kind": kind,
            "value": Decimal(value),
            "unit": unit,
            "effective_from": date(2026, 1, 1),
            "effective_to": date(2027, 1, 1),
            "source_id": "synthetic-award-1",
            "source_sha256": "a" * 64,
            "citation": "synthetic clause 1",
            "status": "accepted",
            "component": identity,
        },
    )


def test_versioned_conditions_create_explicit_hourly_breakdown() -> None:
    """Salary, annual allowance and salary-only loading have transparent bases."""
    release = ConditionRelease(
        release_id="example-v2",
        jurisdiction="QLD",
        employer="Synthetic employer",
        classification="Synthetic grade",
        sources=SourceRegistry(records=(source(),)),
        conditions=(
            condition("salary", "salary", "100000", "AUD/year"),
            condition("hours", "paid_hours", "2000", "hours/year"),
            condition("allowance", "fixed_annual", "2000", "AUD/year"),
            condition("super", "salary_fraction", "0.1", "fraction"),
        ),
    )
    assert_that(
        hourly_components(release, date(2026, 6, 1))
        == {
            "salary": Decimal(50),
            "allowance": Decimal(1),
            "super": Decimal(5),
        },
    )


def test_unaccepted_or_uncovered_condition_fails_closed() -> None:
    """Candidate values and dates beyond their evidence cannot become rates."""
    baseline = condition("salary", "salary", "100000", "AUD/year")
    candidate = baseline.model_copy(update={"status": "candidate"})
    with pytest.raises(ValueError, match="accepted"):
        ConditionRelease(
            release_id="bad",
            jurisdiction="QLD",
            employer="Synthetic employer",
            classification="Synthetic grade",
            sources=SourceRegistry(records=(source(),)),
            conditions=(candidate,),
        )
    with pytest.raises(ValueError, match="unit"):
        condition("salary", "salary", "100000", "fraction")


def test_condition_costing_follows_effective_dates_and_preserves_lineage() -> None:
    """A multi-day activity uses the reviewed conditions applicable on each day."""
    salary = condition("salary", "salary", "100000", "AUD/year")
    paid = condition("hours", "paid_hours", "2000", "hours/year")
    first = condition("allowance-first", "fixed_annual", "2000", "AUD/year").model_copy(
        update={"component": "allowance", "effective_to": date(2026, 6, 2)},
    )
    second = condition(
        "allowance-second",
        "fixed_annual",
        "4000",
        "AUD/year",
    ).model_copy(
        update={"component": "allowance", "effective_from": date(2026, 6, 2)},
    )
    release = ConditionRelease(
        release_id="version-1",
        jurisdiction="QLD",
        employer="Synthetic employer",
        classification="Synthetic grade",
        sources=SourceRegistry(records=(source(),)),
        conditions=(salary, paid, first, second),
    )
    activity = Activity(
        activity_id="shift",
        resource_id="nurse",
        starts_at=datetime(2026, 6, 1, 23, tzinfo=UTC),
        ends_at=datetime(2026, 6, 2, 1, tzinfo=UTC),
        resources=Decimal(1),
    )
    result = cost_condition_activity(release, activity, "UTC")
    assert_that(result.total == Decimal(103))
    expected_segments = 2
    assert_that(len(result.segments) == expected_segments)
    assert_that(
        result.segments[0].condition_ids == ("salary", "hours", "allowance-first"),
    )
    assert_that(
        result.segments[1].condition_ids == ("salary", "hours", "allowance-second"),
    )


def test_condition_costing_uses_elapsed_hours_across_dst() -> None:
    """A repeated local hour is charged for actual elapsed time, without inference."""
    release = ConditionRelease(
        release_id="dst",
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
        activity_id="dst-shift",
        resource_id="staff",
        starts_at=datetime(2026, 4, 4, 15, tzinfo=UTC),
        ends_at=datetime(2026, 4, 4, 18, tzinfo=UTC),
        resources=Decimal(1),
    )
    result = cost_condition_activity(release, activity, "Australia/Sydney")
    assert_that(result.total == Decimal(150))
    assert_that(
        sum((segment.hours for segment in result.segments), Decimal(0)) == Decimal(3),
    )


def test_condition_release_rejects_overlap_and_source_horizon() -> None:
    """Conditions cannot overlap on a component or outlive verified source scope."""
    salary = condition("salary", "salary", "100000", "AUD/year")
    overlap = salary.model_copy(update={"condition_id": "salary-2"})
    with pytest.raises(ValueError, match="Overlapping"):
        ConditionRelease(
            release_id="overlap",
            jurisdiction="QLD",
            employer="Synthetic employer",
            classification="Synthetic grade",
            sources=SourceRegistry(records=(source(),)),
            conditions=(salary, overlap),
        )
    expired = salary.model_copy(update={"effective_to": date(2027, 1, 2)})
    with pytest.raises(ValueError, match="coverage"):
        ConditionRelease(
            release_id="expired",
            jurisdiction="QLD",
            employer="Synthetic employer",
            classification="Synthetic grade",
            sources=SourceRegistry(records=(source(),)),
            conditions=(expired,),
        )
