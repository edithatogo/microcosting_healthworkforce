# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Synthetic allowance and on-cost dependencies with exact arithmetic."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from fractions import Fraction

import pytest

from src.conditions import ConditionRelease
from src.costing import Activity
from src.derived_components import (
    DerivedComponentRule,
    cost_derived_activity,
    cost_derived_snapshot,
)
from tests.checks import assert_that
from tests.test_conditions import condition
from tests.test_roster_costing import release


def baseline() -> ConditionRelease:
    """Use a synthetic 50/hour salary and 10 percent base superannuation."""
    old = release()
    return ConditionRelease.model_validate(
        {
            **old.model_dump(),
            "conditions": (
                *old.conditions,
                condition("super", "salary_fraction", "0.1", "fraction"),
            ),
        },
    )


def rule(
    identity: str,
    component: str,
    bases: tuple[str, ...],
    fraction: str,
) -> DerivedComponentRule:
    """Construct a synthetic reviewed additive dependency."""
    return DerivedComponentRule(
        rule_id=identity,
        component=component,
        bases=bases,
        fraction=Decimal(fraction),
        source_id="synthetic-award-1",
        source_sha256="a" * 64,
        citation="synthetic condition",
        effective_from=date(2026, 1, 1),
        effective_to=date(2027, 1, 1),
        reviewed=True,
    )


def test_allowance_and_incremental_oncost_are_added_once() -> None:
    """50 salary + 5 base super + 2.50 allowance + .25 super = 57.75."""
    rules = (
        rule("allowance-rule", "allowance", ("salary",), "0.05"),
        rule("oncost-rule", "allowance_super", ("allowance",), "0.1"),
    )
    result = cost_derived_snapshot(baseline(), date(2026, 6, 2), Decimal(1), rules)
    assert_that(result.exact_total == Fraction(231, 4))
    assert_that([row.amount for row in result.rows] == [Fraction(5, 2), Fraction(1, 4)])
    assert_that(result.base.total == Decimal(55))


def test_dynamic_and_static_match_at_constant_dates() -> None:
    """The dated activity and nominal snapshot share exact component logic."""
    rules = (
        rule("allowance-rule", "allowance", ("salary",), "0.05"),
        rule("oncost-rule", "allowance_super", ("allowance",), "0.1"),
    )
    start = datetime(2026, 6, 2, 9, tzinfo=UTC)
    activity = Activity(
        activity_id="a",
        resource_id="worker",
        starts_at=start,
        ends_at=start + timedelta(hours=2),
        resources=Decimal(1),
    )
    dynamic = cost_derived_activity(baseline(), activity, "UTC", rules)
    static = cost_derived_snapshot(baseline(), date(2026, 6, 2), Decimal(2), rules)
    assert_that(dynamic.exact_total == static.exact_total == Fraction(231, 2))


def test_unknown_order_duplicate_and_unreviewed_rules_fail_closed() -> None:
    """No dependency, source or component is inferred or silently overwritten."""
    allowance = rule("allowance", "allowance", ("salary",), "0.05")
    oncost = rule("oncost", "allowance_super", ("allowance",), "0.1")
    with pytest.raises(ValueError, match="missing or not yet"):
        cost_derived_snapshot(
            baseline(),
            date(2026, 6, 2),
            Decimal(1),
            (oncost, allowance),
        )
    with pytest.raises(ValueError, match="unique"):
        cost_derived_snapshot(
            baseline(),
            date(2026, 6, 2),
            Decimal(1),
            (allowance, allowance),
        )
    with pytest.raises(ValueError, match="hash"):
        cost_derived_snapshot(
            baseline(),
            date(2026, 6, 2),
            Decimal(1),
            (allowance.model_copy(update={"source_sha256": "b" * 64}),),
        )
    with pytest.raises(ValueError, match="reviewed"):
        cost_derived_snapshot(
            baseline(),
            date(2026, 6, 2),
            Decimal(1),
            (allowance.model_copy(update={"reviewed": False}),),
        )


def test_activity_rejects_rule_expiring_mid_shift() -> None:
    """A dated rule is checked for every local-day segment."""
    start = datetime(2026, 6, 2, 23, tzinfo=UTC)
    activity = Activity(
        activity_id="night",
        resource_id="worker",
        starts_at=start,
        ends_at=start + timedelta(hours=2),
        resources=Decimal(1),
    )
    expiring = rule("allowance-rule", "allowance", ("salary",), "0.05").model_copy(
        update={"effective_to": date(2026, 6, 3)},
    )
    with pytest.raises(ValueError, match="costing date"):
        cost_derived_activity(baseline(), activity, "UTC", (expiring,))


def test_budget_premiums_feed_distinct_oncost_bases() -> None:
    """Synthetic budget fractions preserve premium exclusions and levy ordering."""
    rules = (
        rule("qualification", "qualification", ("salary",), "0.2"),
        rule("overtime", "overtime", ("salary", "qualification"), "0.1"),
        rule("penalty", "penalty", ("salary", "qualification"), "0.05"),
        rule("premium_super", "premium_super", ("qualification", "penalty"), "0.1"),
        rule(
            "levy",
            "levy",
            ("salary", "qualification", "overtime", "penalty"),
            "0.02",
        ),
        rule(
            "insurance",
            "insurance",
            (
                "salary",
                "super",
                "qualification",
                "overtime",
                "penalty",
                "premium_super",
                "levy",
            ),
            "0.01",
        ),
    )
    day = date(2026, 6, 2)
    snapshot = cost_derived_snapshot(baseline(), day, Decimal(1), rules)
    start = datetime(2026, 6, 2, 9, tzinfo=UTC)
    activity = Activity(
        activity_id="budget-comparison",
        resource_id="worker",
        starts_at=start,
        ends_at=start + timedelta(hours=1),
        resources=Decimal(1),
    )
    dynamic = cost_derived_activity(baseline(), activity, "UTC", rules)

    assert_that(
        [row.base_hourly for row in snapshot.rows]
        == [
            Fraction(50),
            Fraction(60),
            Fraction(60),
            Fraction(13),
            Fraction(69),
            Fraction("76.68"),
        ],
    )
    assert_that(snapshot.exact_total == dynamic.exact_total == Fraction("77.4468"))

    # Removing one premium isolates its direct and downstream contribution.
    for index, expected_delta in ((1, "6.1812"), (2, "3.3936")):
        without_premium = (
            *rules[:index],
            rules[index].model_copy(update={"fraction": Decimal(0)}),
            *rules[index + 1 :],
        )
        reduced_snapshot = cost_derived_snapshot(
            baseline(),
            day,
            Decimal(1),
            without_premium,
        )
        reduced_activity = cost_derived_activity(
            baseline(),
            activity,
            "UTC",
            without_premium,
        )
        assert_that(
            snapshot.exact_total - reduced_snapshot.exact_total
            == Fraction(expected_delta),
        )
        assert_that(
            dynamic.exact_total - reduced_activity.exact_total
            == Fraction(expected_delta),
        )


def test_grossed_up_backfill_remains_visible_in_downstream_bases() -> None:
    """Expose nested on-costs when a grossed-up component enters super again."""
    rules = (
        rule("backfill", "backfill", ("salary",), "0.2323"),
        rule("backfill_super", "backfill_super", ("backfill",), "0.1"),
        rule("backfill_cover", "backfill_cover", ("backfill_super",), "0.01"),
    )
    result = cost_derived_snapshot(baseline(), date(2026, 6, 2), Decimal(2), rules)
    backfill, super_cost, cover = result.rows
    assert_that(backfill.amount == Fraction("23.23"))
    assert_that(super_cost.amount == Fraction("2.323"))
    assert_that(cover.amount == Fraction("0.02323"))
    assert_that(result.exact_total == Fraction("135.57623"))


def test_casual_budget_loading_is_visible_in_selected_bases() -> None:
    """Count the salary increment once and trace its selected dependencies."""
    rules = (
        rule("casual", "casual", ("salary",), "0.25"),
        rule("penalty", "penalty", ("salary", "casual"), "0.1"),
        rule("loaded_super", "loaded_super", ("casual", "penalty"), "0.1"),
    )
    start = datetime(2026, 6, 2, 9, tzinfo=UTC)
    activity = Activity(
        activity_id="casual-budget",
        resource_id="worker",
        starts_at=start,
        ends_at=start + timedelta(hours=1),
        resources=Decimal(1),
    )
    snapshot = cost_derived_snapshot(baseline(), start.date(), Decimal(1), rules)
    dynamic = cost_derived_activity(baseline(), activity, "UTC", rules)

    assert_that(
        [row.amount for row in snapshot.rows]
        == [Fraction("12.5"), Fraction("6.25"), Fraction("1.875")],
    )
    assert_that(dynamic.rows == snapshot.rows)
    assert_that(dynamic.exact_total == snapshot.exact_total == Fraction("75.625"))


def test_budget_premium_distinguishes_explicit_zero_from_missing() -> None:
    """An explicit zero retains its base and provenance in the scenario ledger."""
    rules = (
        rule("qualification", "qualification", ("salary",), "0.2"),
        rule("overtime", "overtime", ("salary", "qualification"), "0.1"),
        rule("penalty", "penalty", ("salary", "qualification"), "0"),
    )
    day = date(2026, 6, 2)
    explicit = cost_derived_snapshot(baseline(), day, Decimal(1), rules)
    omitted = cost_derived_snapshot(baseline(), day, Decimal(1), rules[:-1])
    assert_that(explicit.exact_total == omitted.exact_total == Fraction(71))
    assert_that(explicit.rows[:-1] == omitted.rows)
    assert_that(explicit.rows[-1].base_hourly == Fraction(60))
    assert_that(explicit.rows[-1].amount == Fraction(0))


def test_leave_levy_uses_only_selected_gross_salary_components() -> None:
    """The levy follows eligible pay, excluding super and insurance."""
    rules = (
        rule("loading", "leave_loading", ("salary",), "0.1"),
        rule("insurance", "insurance", ("salary", "super"), "0.02"),
        rule("levy", "leave_levy", ("salary", "leave_loading"), "0.026"),
    )
    day = date(2026, 6, 2)
    start = datetime(2026, 6, 2, 9, tzinfo=UTC)
    activity = Activity(
        activity_id="levy-example",
        resource_id="worker",
        starts_at=start,
        ends_at=start + timedelta(hours=2),
        resources=Decimal(1),
    )
    snapshot = cost_derived_snapshot(baseline(), day, Decimal(2), rules)
    dated = cost_derived_activity(baseline(), activity, "UTC", rules)
    assert_that(snapshot.rows[-1].base_hourly == Fraction(55))
    assert_that(snapshot.rows[-1].amount == Fraction("2.86"))
    assert_that(dated.rows == snapshot.rows)
    assert_that(dated.exact_total == snapshot.exact_total == Fraction("125.06"))


def test_backfill_scenario_separates_direct_cost_and_loaded_super_base() -> None:
    """Retain direct backfill, its on-costs and downstream super separately."""
    rules = (
        rule("relief", "direct_backfill", ("salary",), "0.02"),
        rule("relief-load", "backfill_oncost", ("direct_backfill",), "0.1615"),
        rule(
            "relief-super",
            "additional_super",
            ("direct_backfill", "backfill_oncost"),
            "0.1",
        ),
    )
    result = cost_derived_snapshot(baseline(), date(2026, 6, 2), Decimal(100), rules)
    assert_that(
        [row.amount for row in result.rows]
        == [Fraction(100), Fraction("16.15"), Fraction("11.615")],
    )
    assert_that(result.exact_total == Fraction("5627.765"))
