# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Synthetic retrospective release selection and frozen replay examples."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from src.condition_history import ConditionHistory, ReleaseEdition, ReleasePin
from src.conditions import (
    ConditionRelease,
    cost_condition_activity,
    cost_condition_snapshot,
)
from src.costing import Activity
from tests.checks import assert_that
from tests.test_conditions import condition
from tests.test_roster_costing import release


def editions() -> tuple[ReleaseEdition, ReleaseEdition]:
    """Construct a later-known correction to one historical effective period."""
    old = release()
    new = ConditionRelease.model_validate(
        {
            **old.model_dump(),
            "release_id": "corrected",
            "conditions": (
                condition("salary", "salary", "110000", "AUD/year"),
                old.conditions[1],
            ),
        },
    )
    return (
        ReleaseEdition(release=old, known_from=date(2026, 1, 1)),
        ReleaseEdition(
            release=new,
            known_from=date(2026, 6, 1),
            supersedes=old.release_id,
        ),
    )


def test_retrospective_correction_and_frozen_replay() -> None:
    """Knowledge date and work date select independently; old pins remain stable."""
    history = ConditionHistory(editions=editions())
    original, pin = history.select(date(2026, 3, 1))
    corrected, _ = history.select(date(2026, 7, 1))
    worked = date(2026, 2, 1)
    assert_that(
        cost_condition_snapshot(original, worked, Decimal(1)).total == Decimal(50),
    )
    assert_that(
        cost_condition_snapshot(corrected, worked, Decimal(1)).total == Decimal(55),
    )
    assert_that(history.replay(pin).release_id == original.release_id)
    assert_that(
        cost_condition_snapshot(history.replay(pin), worked, Decimal(1)).total
        == Decimal(50),
    )


def test_replay_rejects_unknown_early_or_changed_release() -> None:
    """A reused identity with changed terms cannot silently alter a prior run."""
    history = ConditionHistory(editions=editions())
    original, pin = history.select(date(2026, 3, 1))
    with pytest.raises(ValueError, match="No release known"):
        history.select(date(2025, 12, 31))
    with pytest.raises(ValueError, match="not known"):
        history.replay(
            ReleasePin(
                release_id="corrected",
                release_sha256=pin.release_sha256,
                knowledge_date=pin.knowledge_date,
            ),
        )
    modified = original.model_copy(
        update={
            "release_id": original.release_id,
            "conditions": editions()[1].release.conditions,
        },
    )
    changed = ConditionHistory(
        editions=(ReleaseEdition(release=modified, known_from=date(2026, 1, 1)),),
    )
    with pytest.raises(ValueError, match="hash mismatch"):
        changed.replay(pin)


def test_history_rejects_ambiguous_or_wrong_scope() -> None:
    """No implicit tie-break, branching or cross-employer release selection."""
    old, new = editions()
    with pytest.raises(ValueError, match="linear"):
        ConditionHistory(
            editions=(old, new.model_copy(update={"known_from": old.known_from})),
        )
    with pytest.raises(ValueError, match="linear"):
        ConditionHistory(editions=(old, new.model_copy(update={"supersedes": "other"})))
    with pytest.raises(ValueError, match="scope"):
        ConditionHistory(
            editions=(
                old,
                new.model_copy(
                    update={
                        "release": new.release.model_copy(update={"employer": "Other"}),
                    },
                ),
            ),
        )


def test_historical_selection_also_applies_to_dynamic_activity() -> None:
    """A pinned version produces reproducible dated activity costs."""
    history = ConditionHistory(editions=editions())
    old, pin = history.select(date(2026, 3, 1))
    later, _ = history.select(date(2026, 7, 1))
    start = datetime(2026, 2, 1, 9, tzinfo=UTC)
    activity = Activity(
        activity_id="a",
        resource_id="worker",
        starts_at=start,
        ends_at=start + timedelta(hours=1),
        resources=Decimal(1),
    )
    assert_that(cost_condition_activity(old, activity, "UTC").total == Decimal(50))
    assert_that(cost_condition_activity(later, activity, "UTC").total == Decimal(55))
    assert_that(
        cost_condition_activity(history.replay(pin), activity, "UTC").total
        == Decimal(50),
    )
