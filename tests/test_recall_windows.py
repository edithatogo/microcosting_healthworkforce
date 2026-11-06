# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Recall scenarios keep anchored guarantees separate from actual work."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

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


def test_elapsed_windows_cross_midnight_without_reset() -> None:
    """Midnight is not a new elapsed-time guarantee for this selected method."""
    start = datetime(2026, 6, 1, 23, 50, tzinfo=UTC)
    events = (
        RecallEvent("a", "worker", start, start + timedelta(minutes=5)),
        RecallEvent(
            "b",
            "worker",
            start + timedelta(minutes=20),
            start + timedelta(minutes=25),
        ),
    )
    result = plan_recall_windows(
        events,
        timedelta(minutes=30),
        "anchored_first_recall_v1",
    )
    assert_that(len(result) == 1)
    assert_that(result[0].worked_microseconds == 10 * MINUTE)
    assert_that(result[0].payable_microseconds == 30 * MINUTE)


def test_dst_fold_and_gap_use_utc_elapsed_duration() -> None:
    """The same 20-minute work interval crosses either Sydney clock transition."""
    zone = ZoneInfo("Australia/Sydney")
    intervals = (
        (
            datetime(2026, 10, 4, 1, 50, tzinfo=zone),
            datetime(2026, 10, 4, 3, 10, tzinfo=zone),
        ),
        (
            datetime(2026, 4, 5, 2, 50, tzinfo=zone, fold=0),
            datetime(2026, 4, 5, 2, 10, tzinfo=zone, fold=1),
        ),
    )
    for start, end in intervals:
        result = plan_recall_windows(
            (RecallEvent("a", "worker", start, end),),
            timedelta(minutes=30),
            "anchored_first_recall_v1",
        )
        assert_that(result[0].worked_microseconds == 20 * MINUTE)
        assert_that(result[0].payable_microseconds == 30 * MINUTE)


def test_invalid_intervals_minimum_and_empty_evidence() -> None:
    """Missing timezone, invalid duration and invalid guarantee fail explicitly."""
    for item, message in [
        (
            RecallEvent("a", "worker", START.replace(tzinfo=None), START),
            "timezone aware",
        ),
        (RecallEvent("a", "worker", START, START), "positive"),
    ]:
        with pytest.raises(ValueError, match=message):
            plan_recall_windows(
                (item,),
                timedelta(minutes=30),
                "anchored_first_recall_v1",
            )
    with pytest.raises(ValueError, match="positive minimum"):
        plan_recall_windows((), timedelta(0), "anchored_first_recall_v1")
    empty = plan_recall_windows((), timedelta(minutes=30), "anchored_first_recall_v1")
    assert_that(empty == ())
