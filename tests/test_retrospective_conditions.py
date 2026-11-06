# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Explicitly reviewed retrospective source evidence for costing releases."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from src.conditions import (
    ConditionRelease,
    cost_condition_activity,
    cost_condition_snapshot,
)
from src.costing import Activity
from src.pay_period_effective import RetrospectiveAuthority
from src.source_registry import SourceRegistry
from tests.checks import assert_that
from tests.test_conditions import condition
from tests.test_source_registry import source


def retrospective_release() -> ConditionRelease:
    """Create a synthetic later-known agreement with earlier salary effect."""
    authority = RetrospectiveAuthority(
        entitlement_from=date(2025, 6, 1),
        entitlement_to=date(2026, 1, 1),
        known_from=date(2026, 1, 1),
        as_known_at=date(2026, 2, 1),
        citation="synthetic retrospective clause",
        reviewed=True,
    )
    values = (
        condition("salary", "salary", "100000", "AUD/year"),
        condition("hours", "paid_hours", "2000", "hours/year"),
    )
    return ConditionRelease(
        release_id="retrospective",
        jurisdiction="QLD",
        employer="Synthetic employer",
        classification="Synthetic grade",
        as_known_at=date(2026, 2, 1),
        sources=SourceRegistry(records=(source(),)),
        conditions=tuple(
            c.model_copy(
                update={"effective_from": date(2025, 6, 1), "retrospective": authority},
            )
            for c in values
        ),
    )


def test_reviewed_retroactive_snapshot_and_activity_agree() -> None:
    """A later-known source can price an explicitly reviewed earlier day."""
    release = retrospective_release()
    start = datetime(2025, 7, 1, 9, tzinfo=UTC)
    snapshot = cost_condition_snapshot(release, start.date(), Decimal(2))
    activity = Activity(
        activity_id="shift",
        resource_id="worker",
        starts_at=start,
        ends_at=start + timedelta(hours=2),
        resources=Decimal(1),
    )
    assert_that(
        snapshot.total == cost_condition_activity(release, activity, "UTC").total,
    )
    assert_that(snapshot.total == Decimal(100))
    assert_that(snapshot.conditions[0].retrospective is not None)


def test_retroactive_scope_hash_and_knowledge_fail_closed() -> None:
    """Reject missing review and incorrect knowledge, scope, hash or period."""
    release = retrospective_release()
    item = release.conditions[0]
    authority = item.retrospective
    if authority is None:
        msg = "Test requires retrospective authority"
        raise ValueError(msg)
    for change, match in (
        ({"as_known_at": None}, "knowledge date"),
        ({"as_known_at": date(2026, 1, 15)}, "knowledge date"),
        ({"employer": "Other employer"}, "scope"),
        (
            {"conditions": (item.model_copy(update={"source_sha256": "b" * 64}),)},
            "hash",
        ),
        ({"conditions": (item.model_copy(update={"retrospective": None}),)}, "scope"),
        (
            {
                "conditions": (
                    item.model_copy(update={"effective_from": date(2025, 5, 31)}),
                ),
            },
            "interval",
        ),
        (
            {
                "conditions": (
                    item.model_copy(
                        update={
                            "retrospective": authority.model_copy(
                                update={"entitlement_to": date(2025, 12, 1)},
                            ),
                        },
                    ),
                ),
            },
            "interval",
        ),
    ):
        with pytest.raises(ValueError, match=match):
            ConditionRelease.model_validate(
                release.model_copy(update=change).model_dump(),
            )
    with pytest.raises(ValueError, match="Retrospective authority"):
        RetrospectiveAuthority.model_validate(
            authority.model_copy(update={"reviewed": False}).model_dump(),
        )
