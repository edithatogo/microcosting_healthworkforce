# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Recall guarantees compose with explicit effective-dated rates."""

from datetime import UTC, datetime, timedelta
from fractions import Fraction

import pytest

from src.recall_costing import cost_recall_windows
from src.recall_windows import RecallEvent
from tests.checks import assert_that
from tests.test_costing import release


def test_recall_window_crosses_rate_change_with_work_separate() -> None:
    """Ten minutes at 50/hour and twenty at 70/hour cost exactly 95/3."""
    start = datetime(2026, 1, 1, 11, 50, tzinfo=UTC)
    events = (
        RecallEvent("a", "worker", start, start + timedelta(minutes=5)),
        RecallEvent(
            "b",
            "worker",
            start + timedelta(minutes=15),
            start + timedelta(minutes=20),
        ),
    )
    result = cost_recall_windows(
        release(),
        "staff",
        events,
        timedelta(minutes=30),
        "anchored_first_recall_v1",
    )
    assert_that(
        Fraction(
            result.ledger.exact_total_numerator,
            result.ledger.exact_total_denominator,
        )
        == Fraction(95, 3),
    )
    assert_that([r.rate_id for r in result.ledger.rows] == ["morning", "afternoon"])
    minute_microseconds = 60 * 1_000_000
    assert_that(result.windows[0].worked_microseconds == 10 * minute_microseconds)
    assert_that(result.windows[0].payable_microseconds == 30 * minute_microseconds)
    assert_that(result.ledger.release_id == "synthetic-1")
    assert_that(result.method_id == "anchored_window_flat_rate_v1")


def test_uncovered_guarantee_fails_even_when_work_is_covered() -> None:
    """Coverage must extend through guaranteed paid time, not only actual work."""
    old = release()
    partial = old.model_copy(update={"rates": (old.rates[0],)})
    start = datetime(2026, 1, 1, 11, 50, tzinfo=UTC)
    with pytest.raises(ValueError, match="coverage"):
        cost_recall_windows(
            partial,
            "staff",
            (RecallEvent("a", "worker", start, start + timedelta(minutes=5)),),
            timedelta(minutes=30),
            "anchored_first_recall_v1",
        )


def test_separate_windows_keep_guarantees_and_no_event_costs_nothing() -> None:
    """Boundary events create two guarantees; empty evidence creates no charge."""
    start = datetime(2026, 1, 1, 10, tzinfo=UTC)
    minimum = timedelta(minutes=30)
    events = tuple(
        RecallEvent(str(index), "worker", instant, instant + timedelta(minutes=5))
        for index, instant in enumerate((start, start + minimum))
    )
    result = cost_recall_windows(
        release(),
        "staff",
        events,
        minimum,
        "anchored_first_recall_v1",
    )
    expected_cost = 50
    expected_windows = 2
    assert_that(result.ledger.total == expected_cost)
    assert_that(len(result.windows) == expected_windows)
    assert_that(
        len({row.activity_id for row in result.ledger.rows}) == expected_windows,
    )
    empty = cost_recall_windows(
        release(),
        "staff",
        (),
        minimum,
        "anchored_first_recall_v1",
    )
    assert_that(empty.windows == ())
    assert_that(empty.ledger.total == 0)
