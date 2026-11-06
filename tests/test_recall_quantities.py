# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Independent quantity examples distinguish work, travel, rounding and minimum."""

from dataclasses import replace
from datetime import timedelta
from fractions import Fraction

import pytest

from src.recall_quantities import RecallQuantityPolicy, quantify_recall
from tests.checks import assert_that

MINUTE = 60000000
POLICY = RecallQuantityPolicy(
    "synthetic-policy",
    timedelta(minutes=15),
    timedelta(minutes=15),
    "half_up",
    timedelta(hours=2),
    "cap_travel_sum_round_then_minimum_v1",
)


def test_capped_journeys_minimum_and_actual_work_are_separate() -> None:
    """20 work + min(25,15) + min(5,15) = 40, rounded45, payable120."""
    result = quantify_recall(
        "event",
        timedelta(minutes=20),
        timedelta(minutes=25),
        timedelta(minutes=5),
        POLICY,
    )
    assert_that(result.worked_microseconds == 20 * MINUTE)
    assert_that(result.outbound_travel_microseconds == 25 * MINUTE)
    assert_that(result.return_travel_microseconds == 5 * MINUTE)
    assert_that(result.eligible_outbound_microseconds == 15 * MINUTE)
    assert_that(result.eligible_return_microseconds == 5 * MINUTE)
    assert_that(result.eligible_microseconds == 40 * MINUTE)
    assert_that(result.rounded_microseconds == 45 * MINUTE)
    assert_that(result.minimum_increment_microseconds == 75 * MINUTE)
    assert_that(result.payable_hours == Fraction(2))


def test_total_is_rounded_once_and_minimum_is_not_rounded() -> None:
    """Three six-minute parts sum18 ->15; an explicit17-minute minimum wins."""
    policy = replace(POLICY, minimum=timedelta(minutes=17))
    result = quantify_recall(
        "a",
        timedelta(minutes=6),
        timedelta(minutes=6),
        timedelta(minutes=6),
        policy,
    )
    assert_that(result.eligible_microseconds == 18 * MINUTE)
    assert_that(result.rounded_microseconds == 15 * MINUTE)
    assert_that(result.rounding_adjustment_microseconds == -3 * MINUTE)
    assert_that(result.minimum_increment_microseconds == 2 * MINUTE)
    assert_that(result.payable_hours == Fraction(17, 60))


@pytest.mark.parametrize(
    ("seconds", "ties", "expected_minutes"),
    [(450, "half_up", 15), (450, "half_even", 0), (1350, "half_even", 30)],
)
def test_half_quantum_choices_are_explicit(
    seconds: int,
    ties: str,
    expected_minutes: int,
) -> None:
    """Ties at7.5/22.5 minutes distinguish away-from-zero and even rounding."""
    policy = replace(POLICY, minimum=timedelta(0))
    if ties == "half_even":
        policy = replace(policy, rounding_ties="half_even")
    result = quantify_recall(
        "tie",
        timedelta(seconds=seconds),
        timedelta(0),
        timedelta(0),
        policy,
    )
    assert_that(result.payable_microseconds == expected_minutes * MINUTE)
    assert_that(result.worked_microseconds == seconds * 1000000)


def test_above_minimum_and_exact_microsecond_boundaries() -> None:
    """No floating seconds: a microsecond either side of the tie changes result."""
    results = [
        quantify_recall(
            "boundary",
            timedelta(minutes=127, seconds=30, microseconds=offset),
            timedelta(0),
            timedelta(0),
            POLICY,
        )
        for offset in (-1, 0, 1)
    ]
    assert_that(
        [r.payable_hours for r in results]
        == [Fraction(2), Fraction(9, 4), Fraction(9, 4)],
    )


@pytest.mark.parametrize(
    "field",
    ["minimum", "travel_cap_each_way", "rounding_quantum"],
)
def test_invalid_policy_durations_fail(field: str) -> None:
    """Invalid durations cannot silently manufacture payable quantities."""
    policy = replace(POLICY, **{field: timedelta(microseconds=-1)})
    with pytest.raises(ValueError, match="positive work"):
        quantify_recall("bad", timedelta(minutes=1), timedelta(0), timedelta(0), policy)


def test_zero_quantum_negative_travel_empty_identity_and_work_fail() -> None:
    """Preserve fail-closed boundaries for missing or impossible evidence."""
    with pytest.raises(ValueError, match="positive work"):
        quantify_recall(
            "a",
            timedelta(minutes=1),
            timedelta(0),
            timedelta(0),
            replace(POLICY, rounding_quantum=timedelta(0)),
        )
    for event_id, work, travel in [
        (" ", timedelta(minutes=1), timedelta(0)),
        ("a", timedelta(0), timedelta(0)),
        ("a", timedelta(minutes=1), timedelta(seconds=-1)),
    ]:
        with pytest.raises(ValueError, match=r"nonblank|positive work"):
            quantify_recall(event_id, work, travel, timedelta(0), POLICY)


def test_each_journey_has_its_own_cap() -> None:
    """A short journey cannot donate its unused allowance to the other direction."""
    policy = replace(
        POLICY,
        minimum=timedelta(0),
        rounding_quantum=timedelta(minutes=1),
    )
    result = quantify_recall(
        "asymmetric",
        timedelta(minutes=10),
        timedelta(minutes=29),
        timedelta(minutes=1),
        policy,
    )
    assert_that(result.payable_hours == Fraction(26, 60))
    reverse = quantify_recall(
        "reverse",
        timedelta(minutes=10),
        timedelta(minutes=1),
        timedelta(minutes=29),
        policy,
    )
    assert_that(result.payable_microseconds == reverse.payable_microseconds)


def test_unsupported_policy_and_missing_policy_identity_fail() -> None:
    """Runtime input is checked even if a caller bypasses static typing."""
    for field, value, message in [
        ("method", "unknown", "Unsupported"),
        ("rounding_ties", "unknown", "tie convention"),
        ("policy_id", " ", "nonblank"),
    ]:
        policy = replace(POLICY)
        object.__setattr__(policy, field, value)
        with pytest.raises(ValueError, match=message):
            quantify_recall(
                "a",
                timedelta(minutes=1),
                timedelta(0),
                timedelta(0),
                policy,
            )
