# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Recall scenarios keep anchored guarantees separate from actual work."""

from datetime import UTC, datetime, timedelta

import pytest

from src.recall_windows import RecallEvent, plan_recall_windows
from tests.checks import assert_that

START = datetime(2026, 6, 1, tzinfo=UTC)
MINUTE = 60000000


def event(identity: str, start: int, end: int) -> RecallEvent:
    """Build a synthetic event in minutes after a fixed UTC instant."""
    return RecallEvent(
        identity,
        "worker",
        START + timedelta(minutes=start),
        START + timedelta(minutes=end),
    )


def test_repeated_contact_and_work_beyond_guarantee() -> None:
    """Two contacts pay one 30-minute window plus five minutes beyond it."""
    groups = plan_recall_windows(
        (event("a", 0, 5), event("b", 25, 35)),
        timedelta(minutes=30),
        "anchored_first_recall_v1",
    )
    assert_that(len(groups) == 1)
    assert_that(groups[0].worked_microseconds == 15 * MINUTE)
    assert_that(groups[0].payable_microseconds == 35 * MINUTE)


def test_boundary_and_anchor_do_not_roll_forward() -> None:
    """Boundary contacts start a new group; earlier contacts do not reset the anchor."""
    groups = plan_recall_windows(
        (event("c", 40, 45), event("a", 0, 5), event("b", 20, 25)),
        timedelta(minutes=30),
        "anchored_first_recall_v1",
    )
    assert_that([len(g.events) for g in groups] == [2, 1])
    boundary = plan_recall_windows(
        (event("a", 0, 5), event("b", 30, 35)),
        timedelta(minutes=30),
        "anchored_first_recall_v1",
    )
    expected_groups = 2
    assert_that(len(boundary) == expected_groups)


def test_duplicate_overlap_and_multiple_workers_fail() -> None:
    """Ambiguous event evidence cannot silently inflate minima."""
    first = event("a", 0, 5)
    for events, message in [
        ((first, first), "unique"),
        ((first, event("b", 4, 8)), "overlap"),
        (
            (first, RecallEvent("b", "other", START, START + timedelta(minutes=1))),
            "one worker",
        ),
    ]:
        with pytest.raises(ValueError, match=message):
            plan_recall_windows(
                events,
                timedelta(minutes=30),
                "anchored_first_recall_v1",
            )
