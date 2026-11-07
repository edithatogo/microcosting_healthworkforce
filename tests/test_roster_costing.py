# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Overtime examples use synthetic conditions, history and rule assertions."""

from datetime import UTC, date, datetime, timedelta, timezone
from decimal import Decimal, localcontext
from fractions import Fraction

import pytest

from src.conditions import ConditionRelease
from src.costing import Activity
from src.roster_costing import OvertimeRule, PayPeriod, cost_overtime_period
from src.source_registry import SourceRegistry
from tests.checks import assert_that
from tests.test_conditions import condition
from tests.test_source_registry import source


def release() -> ConditionRelease:
    """Return synthetic source-backed conditions."""
    return ConditionRelease(
        release_id="synthetic",
        jurisdiction="QLD",
        employer="Synthetic employer",
        classification="Synthetic grade",
        sources=SourceRegistry(records=(source(),)),
        conditions=(
            condition("salary", "salary", "100000", "AUD/year"),
            condition("hours", "paid_hours", "2000", "hours/year"),
        ),
    )


def period() -> PayPeriod:
    """Return a synthetic period with prior hours."""
    return PayPeriod(
        starts_at=datetime(2026, 6, 1, tzinfo=UTC),
        ends_at=datetime(2026, 6, 8, tzinfo=UTC),
        prior_hours=Decimal(39),
        history_through=datetime(2026, 6, 2, 9, tzinfo=UTC),
        history_complete=True,
    )


def rule() -> OvertimeRule:
    """Return a synthetic overtime rule."""
    return OvertimeRule(
        rule_id="synthetic-overtime",
        threshold_hours=Decimal(40),
        multiplier=Decimal("1.5"),
        source_id="synthetic-award-1",
        source_sha256="a" * 64,
        citation="synthetic clause",
        effective_from=date(2026, 1, 1),
        effective_to=date(2027, 1, 1),
        reviewed=True,
    )


def test_prior_hours_and_threshold_determine_overtime() -> None:
    """One ordinary and one overtime hour at $50/hour cost $125."""
    activity = Activity(
        activity_id="shift",
        resource_id="worker",
        starts_at=datetime(2026, 6, 2, 9, tzinfo=UTC),
        ends_at=datetime(2026, 6, 2, 11, tzinfo=UTC),
        resources=Decimal(1),
    )
    result = cost_overtime_period(release(), period(), rule(), (activity,), "UTC")
    assert_that(result.total == Decimal(125))
    assert_that(result.overtime_hours == Decimal(1))
    assert_that(result.rows[0].condition_ids == ("salary", "hours"))
    assert_that(result.rows[0].rule_id == "synthetic-overtime")


def test_pay_period_start_requires_zero_prior_hours() -> None:
    """Equivalent timestamps cannot carry hours from a previous period."""
    current = period()
    boundary = current.starts_at.astimezone(timezone(timedelta(hours=10)))
    fields = current.model_dump() | {"history_through": boundary}
    with pytest.raises(ValueError, match="Prior hours must be zero"):
        PayPeriod.model_validate(fields)
    PayPeriod.model_validate(fields | {"prior_hours": Decimal(0)})


def test_incomplete_history_and_overlapping_shifts_are_rejected() -> None:
    """No guessed history or duplicate worker allocation enters overtime."""
    activity = Activity(
        activity_id="a",
        resource_id="worker",
        starts_at=datetime(2026, 6, 2, 9, tzinfo=UTC),
        ends_at=datetime(2026, 6, 2, 11, tzinfo=UTC),
        resources=Decimal(1),
    )
    with pytest.raises(ValueError, match="history"):
        cost_overtime_period(
            release(),
            period().model_copy(update={"history_complete": False}),
            rule(),
            (activity,),
            "UTC",
        )
    with pytest.raises(ValueError, match="overlap"):
        cost_overtime_period(
            release(),
            period(),
            rule(),
            (activity, activity.model_copy(update={"activity_id": "b"})),
            "UTC",
        )


def test_overtime_is_invariant_to_adjacent_activity_segmentation() -> None:
    """A threshold crossing produces the same total when a shift is split."""
    first = Activity(
        activity_id="first",
        resource_id="worker",
        starts_at=datetime(2026, 6, 2, 9, tzinfo=UTC),
        ends_at=datetime(2026, 6, 2, 10, tzinfo=UTC),
        resources=Decimal(1),
    )
    second = Activity(
        activity_id="second",
        resource_id="worker",
        starts_at=datetime(2026, 6, 2, 10, tzinfo=UTC),
        ends_at=datetime(2026, 6, 2, 11, tzinfo=UTC),
        resources=Decimal(1),
    )
    combined = first.model_copy(update={"ends_at": second.ends_at})
    whole = cost_overtime_period(release(), period(), rule(), (combined,), "UTC")
    split = cost_overtime_period(release(), period(), rule(), (first, second), "UTC")
    assert_that(whole.total == split.total == Decimal(125))
    assert_that(whole.overtime_hours == split.overtime_hours == Decimal(1))


def test_overtime_rule_rejects_missing_source_or_unbounded_activity() -> None:
    """A source mismatch and pay-period crossing fail instead of extrapolating."""
    activity = Activity(
        activity_id="shift",
        resource_id="worker",
        starts_at=datetime(2026, 6, 2, 9, tzinfo=UTC),
        ends_at=datetime(2026, 6, 2, 11, tzinfo=UTC),
        resources=Decimal(1),
    )
    with pytest.raises(ValueError, match="hash"):
        cost_overtime_period(
            release(),
            period(),
            rule().model_copy(update={"source_sha256": "b" * 64}),
            (activity,),
            "UTC",
        )
    with pytest.raises(ValueError, match="outside"):
        cost_overtime_period(
            release(),
            period(),
            rule(),
            (
                activity.model_copy(
                    update={"ends_at": datetime(2026, 6, 9, tzinfo=UTC)},
                ),
            ),
            "UTC",
        )


def test_overtime_exact_total_is_invariant_for_fractional_hour_splits() -> None:
    """A one-hour shift and three 20-minute shifts agree exactly across a threshold."""
    current_rule = rule().model_copy(update={"threshold_hours": Decimal("39.5")})
    starts = datetime(2026, 6, 2, 9, tzinfo=UTC)
    end = starts + timedelta(hours=1)
    whole = Activity(
        activity_id="whole",
        resource_id="worker",
        starts_at=starts,
        ends_at=end,
        resources=Decimal(1),
    )
    parts = tuple(
        Activity(
            activity_id=str(i),
            resource_id="worker",
            starts_at=starts + timedelta(minutes=i),
            ends_at=starts + timedelta(minutes=i + 20),
            resources=Decimal(1),
        )
        for i in (0, 20, 40)
    )
    a = cost_overtime_period(release(), period(), current_rule, (whole,), "UTC")
    b = cost_overtime_period(release(), period(), current_rule, parts, "UTC")
    with localcontext() as context:
        context.prec = 2
        low_precision = cost_overtime_period(
            release(),
            period(),
            current_rule,
            parts,
            "UTC",
        )
        all_ordinary = cost_overtime_period(release(), period(), rule(), parts, "UTC")
        all_overtime = cost_overtime_period(
            release(),
            period(),
            rule().model_copy(update={"threshold_hours": Decimal(39)}),
            parts,
            "UTC",
        )
    assert_that(all_ordinary.ordinary_hours == Decimal(1))
    assert_that(all_overtime.overtime_hours == Decimal(1))
    assert_that(low_precision.total == Decimal(62))
    assert_that(low_precision.rows[1].ordinary_hours == Decimal("0.17"))
    assert_that(low_precision.rows[1].overtime_hours == Decimal("0.17"))
    expected = Fraction(125, 2)
    assert_that(
        Fraction(a.exact_total_numerator, a.exact_total_denominator) == expected,
    )
    assert_that(
        Fraction(a.exact_total_numerator, a.exact_total_denominator)
        == Fraction(b.exact_total_numerator, b.exact_total_denominator),
    )


def test_overtime_rejects_multiple_or_incomplete_allocation_identities() -> None:
    """One pay period cannot combine separate or unidentified workers."""
    first = Activity(
        activity_id="first",
        resource_id="worker",
        allocation_id="person-1",
        starts_at=datetime(2026, 6, 2, 9, tzinfo=UTC),
        ends_at=datetime(2026, 6, 2, 10, tzinfo=UTC),
        resources=Decimal(1),
    )
    later = first.model_copy(
        update={
            "activity_id": "later",
            "starts_at": first.ends_at,
            "ends_at": datetime(2026, 6, 2, 11, tzinfo=UTC),
            "allocation_id": "person-2",
        },
    )
    with pytest.raises(ValueError, match="allocation"):
        cost_overtime_period(release(), period(), rule(), (first, later), "UTC")
    with pytest.raises(ValueError, match="allocation"):
        cost_overtime_period(
            release(),
            period(),
            rule(),
            (first, later.model_copy(update={"allocation_id": None})),
            "UTC",
        )
    same = later.model_copy(update={"allocation_id": "person-1"})
    assert_that(
        cost_overtime_period(release(), period(), rule(), (first, same), "UTC").total
        == Decimal(125),
    )
