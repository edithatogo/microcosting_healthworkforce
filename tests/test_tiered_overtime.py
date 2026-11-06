# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Synthetic cumulative overtime tiers with explicit evidence and history."""

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from src.costing import Activity
from src.roster_costing import PayPeriod
from src.tiered_overtime import OvertimeTier, TieredOvertimeRule, cost_tiered_overtime
from tests.checks import assert_that
from tests.test_roster_costing import release


def test_two_cumulative_tiers_apply_only_incremental_premiums() -> None:
    """Eight $50 hours with tiers after 40 and 42 hours cost $650."""
    period = PayPeriod(
        starts_at=datetime(2026, 6, 1, tzinfo=UTC),
        ends_at=datetime(2026, 6, 8, tzinfo=UTC),
        prior_hours=Decimal(38),
        history_through=datetime(2026, 6, 2, 9, tzinfo=UTC),
        history_complete=True,
    )
    activity = Activity(
        activity_id="shift",
        resource_id="worker",
        starts_at=datetime(2026, 6, 2, 9, tzinfo=UTC),
        ends_at=datetime(2026, 6, 2, 17, tzinfo=UTC),
        resources=Decimal(1),
    )
    rule = TieredOvertimeRule(
        rule_id="example",
        tiers=(
            OvertimeTier(threshold_hours=Decimal(40), multiplier=Decimal("1.5")),
            OvertimeTier(threshold_hours=Decimal(42), multiplier=Decimal(2)),
        ),
        source_id="synthetic-award-1",
        source_sha256="a" * 64,
        citation="synthetic clause",
        effective_from=date(2026, 1, 1),
        effective_to=date(2027, 1, 1),
        reviewed=True,
    )
    result = cost_tiered_overtime(release(), period, rule, (activity,), "UTC")
    assert_that(result.base_cost == Decimal(400))
    assert_that(result.total == Decimal(650))
    assert_that([x.premium for x in result.tiers] == [Decimal(150), Decimal(100)])
    assert_that([x.hours_at_or_above for x in result.tiers] == [Decimal(6), Decimal(4)])


def test_unordered_or_decreasing_tiers_are_rejected() -> None:
    """The additive method cannot silently represent decreasing multipliers."""
    with pytest.raises(ValueError, match="tier"):
        TieredOvertimeRule(
            rule_id="bad",
            tiers=(
                OvertimeTier(threshold_hours=Decimal(40), multiplier=Decimal(2)),
                OvertimeTier(threshold_hours=Decimal(42), multiplier=Decimal("1.5")),
            ),
            source_id="synthetic-award-1",
            source_sha256="a" * 64,
            citation="synthetic clause",
            effective_from=date(2026, 1, 1),
            effective_to=date(2027, 1, 1),
            reviewed=True,
        )


def test_duplicate_thresholds_and_unreviewed_rule_are_rejected() -> None:
    """Tier identities cannot overlap, and source review is still required."""
    same = (
        OvertimeTier(threshold_hours=Decimal(40), multiplier=Decimal("1.5")),
        OvertimeTier(threshold_hours=Decimal(40), multiplier=Decimal(2)),
    )
    common = {
        "rule_id": "synthetic",
        "source_id": "synthetic-award-1",
        "source_sha256": "a" * 64,
        "citation": "clause",
        "effective_from": date(2026, 1, 1),
        "effective_to": date(2027, 1, 1),
        "reviewed": True,
    }
    with pytest.raises(ValueError, match="tier"):
        TieredOvertimeRule.model_validate({**common, "tiers": same})
    good = TieredOvertimeRule.model_validate({**common, "tiers": (same[0],)})
    period = PayPeriod(
        starts_at=datetime(2026, 6, 1, tzinfo=UTC),
        ends_at=datetime(2026, 6, 8, tzinfo=UTC),
        prior_hours=Decimal(40),
        history_through=datetime(2026, 6, 2, 9, tzinfo=UTC),
        history_complete=True,
    )
    activity = Activity(
        activity_id="shift",
        resource_id="worker",
        starts_at=datetime(2026, 6, 2, 9, tzinfo=UTC),
        ends_at=datetime(2026, 6, 2, 10, tzinfo=UTC),
        resources=Decimal(1),
    )
    with pytest.raises(ValueError, match="review"):
        cost_tiered_overtime(
            release(),
            period,
            good.model_copy(update={"reviewed": False}),
            (activity,),
            "UTC",
        )
