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
