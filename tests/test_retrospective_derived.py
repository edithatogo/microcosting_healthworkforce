# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Synthetic interaction of retrospective conditions and derived rules."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from fractions import Fraction

import pytest

from src.costing import Activity
from src.derived_components import cost_derived_activity, cost_derived_snapshot
from tests.checks import assert_that
from tests.test_derived_components import rule
from tests.test_retrospective_conditions import retrospective_release


def test_reviewed_retrospective_derived_component_static_dynamic() -> None:
    """A reviewed five-percent allowance uses the separately reviewed salary."""
    release = retrospective_release()
    authority = release.conditions[0].retrospective
    if authority is None:
        msg = "Test requires retrospective authority"
        raise ValueError(msg)
    allowance = rule("allowance", "allowance", ("salary",), "0.05").model_copy(
        update={"effective_from": date(2025, 6, 1), "retrospective": authority},
    )
    start = datetime(2025, 7, 1, 9, tzinfo=UTC)
    activity = Activity(
        activity_id="shift",
        resource_id="worker",
        starts_at=start,
        ends_at=start + timedelta(hours=2),
        resources=Decimal(1),
    )
    static = cost_derived_snapshot(release, start.date(), Decimal(2), (allowance,))
    dynamic = cost_derived_activity(release, activity, "UTC", (allowance,))
    assert_that(static.exact_total == dynamic.exact_total == Fraction(105))
    assert_that(static.rows[0].amount == Fraction(5))
    for changes, match in (
        ({"retrospective": None}, "scope"),
        ({"source_sha256": "b" * 64}, "hash"),
        (
            {
                "retrospective": authority.model_copy(
                    update={"as_known_at": date(2026, 3, 1)},
                ),
            },
            "knowledge date",
        ),
        (
            {
                "retrospective": authority.model_copy(
                    update={"entitlement_from": date(2025, 8, 1)},
                ),
            },
            "interval",
        ),
    ):
        with pytest.raises(ValueError, match=match):
            cost_derived_snapshot(
                release,
                start.date(),
                Decimal(1),
                (allowance.model_copy(update=changes),),
            )
