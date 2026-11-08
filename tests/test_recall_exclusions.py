# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Recall payment exclusions retain original intervals and explicit carry-over."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from fractions import Fraction
from zoneinfo import ZoneInfo

import pytest

from src.recall_exclusions import (
    RecallEpisode,
    RecallHistory,
    RecallSegment,
    cost_eligible_recalls,
    partition_repeat_recalls,
)
from tests.checks import assert_that
from tests.test_costing import release

START = datetime(2026, 1, 1, 10, tzinfo=UTC)
MINUTE = 60000000
METHOD = "previous_commencement_half_open_v1"


def episode(identity: str, start: int, end: int) -> RecallEpisode:
    """Build a synthetic episode whose commencement is its work start."""
    return RecallEpisode(
        identity,
        "worker",
        START + timedelta(minutes=start),
        (
            RecallSegment(
                identity + ":work",
                "work",
                START + timedelta(minutes=start),
                START + timedelta(minutes=end),
            ),
        ),
    )


def history() -> RecallHistory:
    """Explicitly attest that no relevant earlier recall is missing."""
    return RecallHistory("worker", START, None, complete=True)


def test_partial_repeat_and_travel_clipping_preserve_evidence() -> None:
    """At minute60, outbound travel is excluded and work retains its final5."""
    second = RecallEpisode(
        "b",
        "worker",
        START + timedelta(minutes=50),
        (
            RecallSegment(
                "b:outbound",
                "outbound_travel",
                START + timedelta(minutes=50),
                START + timedelta(minutes=55),
            ),
            RecallSegment(
                "b:work",
                "work",
                START + timedelta(minutes=55),
                START + timedelta(minutes=65),
            ),
            RecallSegment(
                "b:return",
                "return_travel",
                START + timedelta(minutes=65),
                START + timedelta(minutes=70),
            ),
        ),
    )
    result = partition_repeat_recalls(
        (episode("a", 0, 5), second),
        timedelta(hours=1),
        history(),
        METHOD,
    )
    parts = result.recalls[1].segments
    assert_that([p.excluded_microseconds for p in parts] == [5 * MINUTE, 5 * MINUTE, 0])
    assert_that([p.eligible_microseconds for p in parts] == [0, 5 * MINUTE, 5 * MINUTE])
    assert_that(parts[1].original.starts_at == START + timedelta(minutes=55))
    assert_that(parts[1].eligible_starts_at == START + timedelta(minutes=60))
    assert_that(result.next_history.previous_commencement == second.commences_at)


def test_each_previous_event_resets_clock_even_when_fully_excluded() -> None:
    """The explicitly selected rolling method differs from first-event grouping."""
    result = partition_repeat_recalls(
        tuple(episode(str(t), t, t + 5) for t in (0, 45, 90)),
        timedelta(hours=1),
        history(),
        METHOD,
    )
    assert_that(
        [r.segments[0].eligible_microseconds for r in result.recalls]
        == [5 * MINUTE, 0, 0],
    )
    assert_that(
        result.recalls[2].previous_commencement == START + timedelta(minutes=45),
    )


def test_exact_boundary_and_zero_exclusion_preserve_work() -> None:
    """Half-open exclusion ends exactly at the boundary, with no epsilon."""
    events = (episode("a", 0, 5), episode("b", 60, 65))
    for exclusion in (timedelta(hours=1), timedelta(0)):
        result = partition_repeat_recalls(events, exclusion, history(), METHOD)
        assert_that(
            all(
                r.segments[0].eligible_microseconds == 5 * MINUTE
                for r in result.recalls
            ),
        )


def test_complete_history_carry_over_matches_one_batch_and_event_order() -> None:
    """Splitting a batch or shuffling input cannot reset the exclusion clock."""
    events = tuple(episode(str(t), t, t + 5) for t in (0, 45, 90, 160))
    whole = partition_repeat_recalls(
        tuple(reversed(events)),
        timedelta(hours=1),
        history(),
        METHOD,
    )
    first = partition_repeat_recalls(events[:2], timedelta(hours=1), history(), METHOD)
    second = partition_repeat_recalls(
        events[2:],
        timedelta(hours=1),
        first.next_history,
        METHOD,
    )
    assert_that(whole.recalls == first.recalls + second.recalls)
    assert_that(whole.next_history == second.next_history)


def test_prior_recall_from_previous_observation_period() -> None:
    """An attested prior commencement clips the first event of a new batch."""
    prior = replace(history(), previous_commencement=START - timedelta(minutes=30))
    result = partition_repeat_recalls(
        (episode("a", 10, 40),),
        timedelta(hours=1),
        prior,
        METHOD,
    )
    part = result.recalls[0].segments[0]
    assert_that(part.excluded_microseconds == 20 * MINUTE)
    assert_that(part.eligible_microseconds == 10 * MINUTE)


def test_effective_dated_price_uses_only_eligible_actual_intervals() -> None:
    """11:30-noon at50 plus noon-12:10 at70 gives110/3, with no guarantee."""
    prior = RecallHistory(
        "worker",
        START + timedelta(minutes=50),
        START + timedelta(minutes=30),
        complete=True,
    )
    plan = partition_repeat_recalls(
        (episode("a", 60, 130),),
        timedelta(hours=1),
        prior,
        METHOD,
    )
    priced = cost_eligible_recalls(release(), "staff", plan)
    assert_that(
        Fraction(
            priced.ledger.exact_total_numerator,
            priced.ledger.exact_total_denominator,
        )
        == Fraction(110, 3),
    )
    assert_that([r.rate_id for r in priced.ledger.rows] == ["morning", "afternoon"])
    assert_that(priced.plan.recalls[0].segments[0].excluded_microseconds == 30 * MINUTE)
    partial = release().model_copy(update={"rates": (release().rates[0],)})
    with pytest.raises(ValueError, match="coverage"):
        cost_eligible_recalls(partial, "staff", plan)


def test_untrusted_derived_partition_is_rejected_before_pricing() -> None:
    """A manually altered eligibility result cannot be treated as trusted input."""
    plan = partition_repeat_recalls(
        (episode("a", 0, 5),),
        timedelta(hours=1),
        history(),
        METHOD,
    )
    recall = plan.recalls[0]
    altered = replace(recall.segments[0], eligible_starts_at=None)
    plan = replace(plan, recalls=(replace(recall, segments=(altered,)),))
    with pytest.raises(ValueError, match="does not match"):
        cost_eligible_recalls(release(), "staff", plan)


def test_missing_history_bad_clock_and_allocation_fail() -> None:
    """An omitted history, future prior clock or different worker is not zero."""
    for prior in (
        replace(history(), complete=False),
        replace(history(), previous_commencement=START),
        replace(history(), observed_from=START.replace(tzinfo=None)),
        replace(history(), allocation_id="other"),
    ):
        with pytest.raises(ValueError, match=r"history|timezone|allocation"):
            partition_repeat_recalls(
                (episode("a", 0, 5),),
                timedelta(hours=1),
                prior,
                METHOD,
            )


def test_duplicate_overlap_and_pre_observation_events_fail() -> None:
    """Reject ambiguous evidence instead of counting it twice."""
    first = episode("a", 0, 5)
    for events in (
        (first, first),
        (first, episode("b", 4, 8)),
        (episode("old", -1, 1),),
    ):
        with pytest.raises(ValueError, match=r"unique|overlap|observation"):
            partition_repeat_recalls(events, timedelta(hours=1), history(), METHOD)


def test_empty_batch_keeps_history_and_has_no_price() -> None:
    """No episode manufactures a minimum or an elapsed exclusion interval."""
    plan = partition_repeat_recalls((), timedelta(hours=1), history(), METHOD)
    assert_that(plan.next_history == history())
    assert_that(cost_eligible_recalls(release(), "staff", plan).ledger.total == 0)


def test_midnight_and_dst_use_elapsed_utc_clocks() -> None:
    """A Sydney clock jump does not create a fresh or longer exclusion window."""
    zone = ZoneInfo("Australia/Sydney")
    starts = [
        datetime(2026, 10, 4, 1, 50, tzinfo=zone),
        datetime(2026, 4, 5, 2, 50, tzinfo=zone, fold=0),
        datetime(2026, 1, 1, 23, 50, tzinfo=zone),
    ]
    for start in starts:
        end = start.astimezone(UTC) + timedelta(minutes=30)
        event = RecallEpisode(
            "a",
            "worker",
            start,
            (RecallSegment("s", "work", start, end),),
        )
        prior = RecallHistory(
            "worker",
            start.astimezone(UTC) - timedelta(minutes=1),
            start.astimezone(UTC) - timedelta(minutes=45),
            complete=True,
        )
        result = partition_repeat_recalls((event,), timedelta(hours=1), prior, METHOD)
        assert_that(result.recalls[0].segments[0].excluded_microseconds == 15 * MINUTE)
        assert_that(result.recalls[0].segments[0].eligible_microseconds == 15 * MINUTE)


def test_segment_splitting_and_order_preserve_time_and_price() -> None:
    """Splitting a work interval cannot remove the cutoff or add payable time."""
    first = episode("a", 0, 5)
    single = episode("b", 50, 80)
    split = replace(
        single,
        segments=(
            RecallSegment(
                "late",
                "work",
                START + timedelta(minutes=70),
                START + timedelta(minutes=80),
            ),
            RecallSegment(
                "early",
                "work",
                START + timedelta(minutes=50),
                START + timedelta(minutes=70),
            ),
        ),
    )
    whole = partition_repeat_recalls(
        (first, single),
        timedelta(hours=1),
        history(),
        METHOD,
    )
    pieces = partition_repeat_recalls(
        (split, first),
        timedelta(hours=1),
        history(),
        METHOD,
    )
    for plan in (whole, pieces):
        parts = plan.recalls[1].segments
        assert_that(sum(p.eligible_microseconds for p in parts) == 20 * MINUTE)
        assert_that(
            sum(p.excluded_microseconds + p.eligible_microseconds for p in parts)
            == 30 * MINUTE,
        )
    assert_that(
        cost_eligible_recalls(release(), "staff", whole).ledger.total
        == cost_eligible_recalls(release(), "staff", pieces).ledger.total,
    )


def test_invalid_segments_and_empty_episodes_fail() -> None:
    """No missing identity, invalid interval or unknown category becomes zero."""
    original = episode("a", 0, 5)
    segment = original.segments[0]
    bad_kind = replace(segment)
    object.__setattr__(bad_kind, "kind", "unknown")
    cases = [
        replace(original, segments=()),
        replace(original, event_id=" "),
        replace(original, segments=(replace(segment, segment_id=" "),)),
        replace(original, segments=(segment, segment)),
        replace(original, segments=(bad_kind,)),
        replace(original, segments=(replace(segment, ends_at=START),)),
        replace(
            original,
            segments=(replace(segment, starts_at=START - timedelta(seconds=1)),),
        ),
        replace(
            original,
            segments=(replace(segment, starts_at=START.replace(tzinfo=None)),),
        ),
    ]
    for item in cases:
        with pytest.raises(
            ValueError,
            match=r"segments|unique|Unsupported|positive|timezone",
        ):
            partition_repeat_recalls((item,), timedelta(hours=1), history(), METHOD)
    with pytest.raises(ValueError, match="nonnegative"):
        partition_repeat_recalls((original,), timedelta(seconds=-1), history(), METHOD)


def test_exclusion_boundary_retains_microsecond_precision() -> None:
    """One microsecond before the boundary is excluded; the following one is not."""
    prior = replace(history(), previous_commencement=START - timedelta(minutes=30))
    cutoff = START + timedelta(minutes=30)
    event = RecallEpisode(
        "a",
        "worker",
        cutoff - timedelta(microseconds=1),
        (
            RecallSegment(
                "tiny",
                "work",
                cutoff - timedelta(microseconds=1),
                cutoff + timedelta(microseconds=1),
            ),
        ),
    )
    result = partition_repeat_recalls((event,), timedelta(hours=1), prior, METHOD)
    part = result.recalls[0].segments[0]
    assert_that(part.excluded_microseconds == part.eligible_microseconds == 1)


def test_interleaved_episode_envelopes_fail_even_without_segment_overlap() -> None:
    """Reject a batch that could not be carried over at an episode boundary."""
    first = replace(
        episode("a", 0, 5),
        segments=(episode("a", 0, 5).segments[0], episode("late", 20, 25).segments[0]),
    )
    with pytest.raises(ValueError, match="envelopes overlap"):
        partition_repeat_recalls(
            (first, episode("b", 10, 15)),
            timedelta(hours=1),
            history(),
            METHOD,
        )


def test_first_commencement_anchor_survives_a_batch_boundary() -> None:
    """A fully excluded second call does not extend the first window."""
    events = tuple(episode(str(t), t, t + 5) for t in (0, 45, 90))
    method = "first_commencement_half_open_v1"
    window = timedelta(hours=1)
    first = partition_repeat_recalls(events[:2], window, history(), method)
    second = partition_repeat_recalls(events[2:], window, first.next_history, method)
    whole = partition_repeat_recalls(events, window, history(), method)
    assert_that(first.recalls + second.recalls == whole.recalls)
    assert_that(second.next_history == whole.next_history)
    assert_that(
        [r.segments[0].eligible_microseconds for r in whole.recalls]
        == [5 * MINUTE, 0, 5 * MINUTE],
    )

    with pytest.raises(ValueError, match="same exclusion method"):
        partition_repeat_recalls(events[2:], window, first.next_history, METHOD)

    with pytest.raises(ValueError, match="same exclusion duration"):
        partition_repeat_recalls(
            events[2:],
            timedelta(minutes=30),
            first.next_history,
            method,
        )
