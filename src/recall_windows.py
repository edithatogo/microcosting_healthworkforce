# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Explicit anchored recall minimum windows with actual work kept separate."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal


@dataclass(frozen=True)
class RecallEvent:
    """One evidenced recall interval for an opaque worker allocation."""

    event_id: str
    allocation_id: str
    starts_at: datetime
    ends_at: datetime


@dataclass(frozen=True)
class RecallWindow:
    """An anchored guarantee plus its original non-overlapping work events."""

    method: str
    allocation_id: str
    starts_at: datetime
    minimum_ends_at: datetime
    paid_ends_at: datetime
    events: tuple[RecallEvent, ...]
    worked_microseconds: int
    payable_microseconds: int


def _micros(value: timedelta) -> int:
    return (value.days * 86400 + value.seconds) * 1000000 + value.microseconds


def _ordered_events(events: tuple[RecallEvent, ...]) -> list[RecallEvent]:
    seen: set[str] = set()
    allocation: str | None = None
    for event in events:
        if not event.event_id.strip() or event.event_id in seen:
            msg = "Recall events require unique nonblank identities"
            raise ValueError(msg)
        seen.add(event.event_id)
        if not event.allocation_id.strip():
            msg = "Recall allocation must be nonblank"
            raise ValueError(msg)
        if allocation is not None and allocation != event.allocation_id:
            msg = "Plan one worker allocation at a time"
            raise ValueError(msg)
        allocation = event.allocation_id
        for instant in (event.starts_at, event.ends_at):
            if instant.tzinfo is None or instant.utcoffset() is None:
                msg = "Recall timestamps must be timezone aware"
                raise ValueError(msg)
        if event.ends_at.astimezone(UTC) <= event.starts_at.astimezone(UTC):
            msg = "Recall work interval must be positive"
            raise ValueError(msg)
    return sorted(events, key=lambda e: e.starts_at.astimezone(UTC))


def plan_recall_windows(
    events: tuple[RecallEvent, ...],
    minimum: timedelta,
    method: Literal["anchored_first_recall_v1"],
) -> tuple[RecallWindow, ...]:
    """Group starts strictly inside the first recall's fixed minimum window.

    The caller selects this method and minimum after qualifying the applicable
    source. Another event does not reset the anchor. Work beyond the guarantee
    extends payable duration. This planner supplies no entitlement or pay rate.
    """
    if method != "anchored_first_recall_v1" or minimum <= timedelta(0):
        msg = "Select the supported method and a positive minimum"
        raise ValueError(msg)
    ordered = _ordered_events(events)
    groups: list[list[RecallEvent]] = []
    prior_end: datetime | None = None
    window_end: datetime | None = None
    for event in ordered:
        start = event.starts_at.astimezone(UTC)
        end = event.ends_at.astimezone(UTC)
        if prior_end is not None and start < prior_end:
            msg = "Recall work intervals overlap"
            raise ValueError(msg)
        if window_end is None or start >= window_end:
            groups.append([])
            window_end = start + minimum
        groups[-1].append(event)
        prior_end = end
    result: list[RecallWindow] = []
    for group in groups:
        start = group[0].starts_at.astimezone(UTC)
        guaranteed_end = start + minimum
        paid_end = max(guaranteed_end, group[-1].ends_at.astimezone(UTC))
        worked = sum(
            _micros(e.ends_at.astimezone(UTC) - e.starts_at.astimezone(UTC))
            for e in group
        )
        result.append(
            RecallWindow(
                method,
                group[0].allocation_id,
                start,
                guaranteed_end,
                paid_end,
                tuple(group),
                worked,
                _micros(paid_end - start),
            ),
        )
    return tuple(result)
