# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Explicit repeat-recall payment exclusions with actual time kept intact."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Literal

from src.costing import Activity, CostRelease, CostResult, cost_dynamic


@dataclass(frozen=True)
class RecallSegment:
    """An original work or travel interval, independently identified."""

    segment_id: str
    kind: Literal["work", "outbound_travel", "return_travel"]
    starts_at: datetime
    ends_at: datetime


@dataclass(frozen=True)
class RecallEpisode:
    """One recall commencement, allocation and its original time evidence."""

    event_id: str
    allocation_id: str
    commences_at: datetime
    segments: tuple[RecallSegment, ...]


@dataclass(frozen=True)
class RecallHistory:
    """An explicitly complete observation boundary and latest earlier clock."""

    allocation_id: str
    observed_from: datetime
    previous_commencement: datetime | None
    complete: bool


@dataclass(frozen=True)
class RecallPartition:
    """Retain the original segment and the first eligible instant, if any."""

    original: RecallSegment
    eligible_starts_at: datetime | None

    @property
    def eligible_microseconds(self) -> int:
        """Return zero only for an explicitly fully excluded segment."""
        if self.eligible_starts_at is None:
            return 0
        return _micros(_utc(self.original.ends_at) - self.eligible_starts_at)

    @property
    def excluded_microseconds(self) -> int:
        """Actual time is conserved as eligible plus excluded time."""
        return (
            _micros(_utc(self.original.ends_at) - _utc(self.original.starts_at))
            - self.eligible_microseconds
        )


@dataclass(frozen=True)
class ExcludedRecall:
    """One original episode, its prior clock and exact segment partitions."""

    episode: RecallEpisode
    previous_commencement: datetime | None
    exclusion_ends_at: datetime | None
    segments: tuple[RecallPartition, ...]


@dataclass(frozen=True)
class RecallExclusionPlan:
    """A selected convention, retained evidence and explicit next-batch history."""

    method: Literal["previous_commencement_half_open_v1"]
    exclusion: timedelta
    history: RecallHistory
    recalls: tuple[ExcludedRecall, ...]
    next_history: RecallHistory


@dataclass(frozen=True)
class EligibleRecallCost:
    """Price only eligible actual intervals, with no guarantee or rounding."""

    plan: RecallExclusionPlan
    ledger: CostResult


def _utc(value: datetime) -> datetime:
    if value.utcoffset() is None:
        msg = "Recall timestamps must be timezone aware"
        raise ValueError(msg)
    return value.astimezone(UTC)


def _micros(value: timedelta) -> int:
    return (value.days * 86400 + value.seconds) * 1000000 + value.microseconds


def _ordered(
    episodes: tuple[RecallEpisode, ...],
    history: RecallHistory,
) -> list[RecallEpisode]:
    boundary = _utc(history.observed_from)
    if history.complete is not True or not history.allocation_id.strip():
        msg = "Recall history requires a complete assertion and allocation"
        raise ValueError(msg)
    if history.previous_commencement is not None and (
        _utc(history.previous_commencement) >= boundary
    ):
        msg = "Prior recall history must precede the observation boundary"
        raise ValueError(msg)
    event_ids: set[str] = set()
    segment_ids: set[str] = set()
    clocks: set[datetime] = set()
    intervals: list[tuple[datetime, datetime]] = []
    for episode in episodes:
        clock = _utc(episode.commences_at)
        if (
            not episode.event_id.strip()
            or episode.event_id in event_ids
            or clock in clocks
        ):
            msg = "Recall IDs/clocks must be unique and nonblank"
            raise ValueError(msg)
        if episode.allocation_id != history.allocation_id:
            msg = "Recall allocation does not match history"
            raise ValueError(msg)
        if clock < boundary or not episode.segments:
            msg = "Recall requires segments at or after the observation boundary"
            raise ValueError(msg)
        event_ids.add(episode.event_id)
        clocks.add(clock)
        for segment in episode.segments:
            _validate_segment(segment, clock, segment_ids)
            intervals.append((_utc(segment.starts_at), _utc(segment.ends_at)))
    prior_end: datetime | None = None
    for start, end in sorted(intervals):
        if prior_end is not None and start < prior_end:
            msg = "Actual recall work and travel intervals overlap"
            raise ValueError(msg)
        prior_end = end
    return sorted(episodes, key=lambda e: _utc(e.commences_at))


def _validate_segment(
    segment: RecallSegment,
    clock: datetime,
    seen: set[str],
) -> None:
    if not segment.segment_id.strip() or segment.segment_id in seen:
        msg = "Recall segments require unique nonblank identities"
        raise ValueError(msg)
    if segment.kind not in ("work", "outbound_travel", "return_travel"):
        msg = "Unsupported recall segment kind"
        raise ValueError(msg)
    if _utc(segment.starts_at) < clock or _utc(segment.ends_at) <= _utc(
        segment.starts_at,
    ):
        msg = "Recall segment must be positive and cannot precede its commencement"
        raise ValueError(msg)
    seen.add(segment.segment_id)


def partition_repeat_recalls(
    episodes: tuple[RecallEpisode, ...],
    exclusion: timedelta,
    history: RecallHistory,
    method: Literal["previous_commencement_half_open_v1"],
) -> RecallExclusionPlan:
    """Exclude time before the immediately previous commencement plus a duration.

    Every episode resets the clock, including one whose segments are completely
    excluded. Intervals are half open and use UTC elapsed time. Commencement is
    caller-supplied, at or before its episode's work/travel. The caller separately
    qualifies this convention and its applicability; no minimum is inferred.
    """
    if method != "previous_commencement_half_open_v1" or exclusion < timedelta(0):
        msg = "Select the supported exclusion method and a nonnegative duration"
        raise ValueError(msg)
    ordered = _ordered(episodes, history)
    previous = (
        _utc(history.previous_commencement)
        if history.previous_commencement is not None
        else None
    )
    recalls: list[ExcludedRecall] = []
    through = _utc(history.observed_from)
    for episode in ordered:
        if _utc(episode.commences_at) < through:
            msg = "Recall episode envelopes overlap; provide sequential episodes"
            raise ValueError(msg)
        cutoff = previous + exclusion if previous is not None else None
        parts: list[RecallPartition] = []
        for segment in sorted(episode.segments, key=lambda s: _utc(s.starts_at)):
            start, end = _utc(segment.starts_at), _utc(segment.ends_at)
            eligible = max(start, cutoff) if cutoff is not None else start
            parts.append(RecallPartition(segment, eligible if eligible < end else None))
            through = max(through, end)
        recalls.append(ExcludedRecall(episode, previous, cutoff, tuple(parts)))
        previous = _utc(episode.commences_at)
    next_history = RecallHistory(
        history.allocation_id,
        through,
        previous,
        complete=True,
    )
    return RecallExclusionPlan(method, exclusion, history, tuple(recalls), next_history)


def cost_eligible_recalls(
    release: CostRelease,
    resource_id: str,
    plan: RecallExclusionPlan,
) -> EligibleRecallCost:
    """Price original eligible instants using the existing effective-dated ledger.

    This deliberately has no travel cap, rounding, minimum, premium-composition
    or source-entitlement inference. Excluded actual work remains in the plan
    and is not deleted from overtime history. Rate/source coverage must span
    every eligible interval. The derived partition is rechecked before costing.
    """
    checked = partition_repeat_recalls(
        tuple(r.episode for r in plan.recalls),
        plan.exclusion,
        plan.history,
        plan.method,
    )
    if checked != plan or not resource_id.strip():
        msg = "Recall partition does not match original evidence or resource identity"
        raise ValueError(msg)
    activities = tuple(
        Activity(
            activity_id="recall-eligible:" + part.original.segment_id,
            resource_id=resource_id,
            allocation_id=recall.episode.allocation_id,
            starts_at=part.eligible_starts_at,
            ends_at=part.original.ends_at,
            resources=Decimal(1),
        )
        for recall in plan.recalls
        for part in recall.segments
        if part.eligible_starts_at is not None
    )
    return EligibleRecallCost(plan, cost_dynamic(release, activities))
