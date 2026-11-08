# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Static source-backed snapshot agrees with dated activity costing."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from fractions import Fraction

import pytest
from pydantic import ValidationError

from src.conditions import (
    PayrollSalaryDivisor,
    cost_condition_activity,
    cost_condition_snapshot,
)
from src.costing import Activity
from tests.checks import assert_that
from tests.test_minimum_engagement import example_release


def test_snapshot_and_constant_activity_agree_with_component_lineage() -> None:
    """Two hours of $50 salary and $1 allowance total $102 in both APIs."""
    release = example_release()
    day = date(2026, 6, 2)
    snapshot = cost_condition_snapshot(release, day, Decimal(2))
    start = datetime(2026, 6, 2, 9, tzinfo=UTC)
    activity = Activity(
        activity_id="shift",
        resource_id="worker",
        starts_at=start,
        ends_at=start + timedelta(hours=2),
        resources=Decimal(1),
    )
    dynamic = cost_condition_activity(release, activity, "UTC")
    assert_that(
        snapshot.components == {"salary": Decimal(100), "allowance": Decimal(2)},
    )
    assert_that(snapshot.total == dynamic.total == Decimal(102))
    assert_that(
        Fraction(snapshot.exact_total_numerator, snapshot.exact_total_denominator)
        == Fraction(dynamic.exact_total_numerator, dynamic.exact_total_denominator),
    )
    assert_that(
        tuple(c.condition_id for c in snapshot.conditions)
        == ("salary", "hours", "allowance"),
    )
    assert_that(
        all(c.source_sha256 == "a" * 64 and c.citation for c in snapshot.conditions),
    )


def test_snapshot_rejects_invalid_quantities_and_uncovered_dates() -> None:
    """No negative, nonfinite or uncovered value becomes a cost."""
    release = example_release()
    for quantity in (Decimal(-1), Decimal("NaN"), Decimal("Infinity")):
        with pytest.raises(ValidationError):
            cost_condition_snapshot(release, date(2026, 6, 2), quantity)
    with pytest.raises(ValueError, match="cover"):
        cost_condition_snapshot(release, date(2027, 1, 1), Decimal(1))
    assert_that(
        cost_condition_snapshot(release, date(2026, 6, 2), Decimal(0)).total == 0,
    )


def test_snapshot_retains_exact_nonterminating_hourly_ratio() -> None:
    """A nonterminating rate retains an exact, segmentation-independent total."""
    original = example_release()
    changed = tuple(
        c.model_copy(update={"value": Decimal(2100)}) if c.kind == "paid_hours" else c
        for c in original.conditions
    )
    release = original.model_copy(update={"conditions": changed})
    snapshot = cost_condition_snapshot(release, date(2026, 6, 2), Decimal(1))
    assert_that(
        Fraction(snapshot.exact_total_numerator, snapshot.exact_total_denominator)
        == Fraction(340, 7),
    )


def test_payroll_basis_snapshot_matches_dynamic_cost() -> None:
    """Use payroll hours for salary and paid hours for the annual allowance."""
    original = example_release()
    divisor = PayrollSalaryDivisor(numerator=5947, denominator=3)
    conditions = tuple(
        item.model_copy(update={"payroll_salary_divisor": divisor})
        if item.kind == "salary"
        else item
        for item in original.conditions
    )
    release = original.model_copy(update={"conditions": conditions})
    start = datetime(2026, 6, 2, 9, tzinfo=UTC)
    snapshot = cost_condition_snapshot(release, start.date(), Decimal(1))
    activity = Activity(
        activity_id="payroll-shift",
        resource_id="worker",
        starts_at=start,
        ends_at=start + timedelta(hours=1),
        resources=Decimal(1),
    )
    dynamic = cost_condition_activity(release, activity, "UTC")
    expected = Fraction(300000, 5947) + 1
    for result in (snapshot, dynamic):
        assert_that(
            Fraction(result.exact_total_numerator, result.exact_total_denominator)
            == expected,
        )
