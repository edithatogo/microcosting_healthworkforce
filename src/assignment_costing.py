# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Price a declared assignment path without inferring promotion or approval."""

import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from fractions import Fraction
from hashlib import sha256
from typing import Literal, Self
from zoneinfo import ZoneInfo
lazy from decimal import Decimal

from pydantic import Field, field_validator, model_validator

from src.condition_history import release_sha256
from src.conditions import (
    ConditionRelease,
    SnapshotQuantity,
    cost_condition_activity,
    cost_condition_snapshot,
    exact_hourly_components,
)
from src.costing import Activity
from src.unit_quotes import QuoteModel


def _instant(value: object) -> datetime:
    """Use explicit instants rather than guessing a local wall-clock offset."""
    if not isinstance(value, datetime) or value.utcoffset() is None:
        msg = "Assignment instants must be timezone-aware datetimes"
        raise ValueError(msg)
    return value.astimezone(UTC)


class AssignmentState(QuoteModel):
    """One bounded assignment and the reviewed decision asserted for it."""

    state_id: str
    starts_at: datetime
    ends_at: datetime
    release: ConditionRelease
    timezone: str
    decision_id: str
    decision_made_on: date
    decision_known_on: date
    earlier_effect_reviewed: bool
    decision_kind: Literal["observed_assignment", "analyst_scenario"]
    decision_basis: str
    decision_reviewed: Literal[True]

    @field_validator("starts_at", "ends_at")
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        """Normalize boundaries before comparing intervals, including DST."""
        return _instant(value)

    @field_validator("timezone")
    @classmethod
    def known_zone(cls, value: str) -> str:
        """Require the explicit local calendar used by condition pricing."""
        try:
            ZoneInfo(value)
        except (KeyError, ValueError) as error:
            msg = "Assignment requires a valid IANA timezone"
            raise ValueError(msg) from error
        return value

    @model_validator(mode="after")
    def valid_state(self) -> Self:
        """Revalidate the nested price release and nonempty interval."""
        if self.ends_at <= self.starts_at:
            msg = "Assignment state must have a nonempty interval"
            raise ValueError(msg)
        if self.decision_known_on < self.decision_made_on:
            msg = "Decision knowledge cannot predate its making date"
            raise ValueError(msg)
        if (
            self.starts_at.astimezone(ZoneInfo(self.timezone)).date()
            < self.decision_made_on
            and not self.earlier_effect_reviewed
        ):
            msg = "Earlier assignment effect requires explicit review"
            raise ValueError(msg)
        ConditionRelease.model_validate(self.release.model_dump())
        return self


class AssignmentTimeline(QuoteModel):
    """A complete declared path for one opaque subject at one knowledge cutoff."""

    timeline_id: str
    subject_id: str
    as_known_on: date
    history_complete: bool
    states: tuple[AssignmentState, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_path(self) -> Self:
        """Reject ambiguous paths, future knowledge and reused release identities."""
        if not self.history_complete:
            msg = "Assignment history must be explicitly complete"
            raise ValueError(msg)
        seen: set[str] = set()
        releases: dict[str, str] = {}
        previous: AssignmentState | None = None
        for state in self.states:
            if state.state_id in seen:
                msg = "Duplicate assignment state identity"
                raise ValueError(msg)
            seen.add(state.state_id)
            if previous is not None and state.starts_at != previous.ends_at:
                msg = "Assignment states require contiguous ordered coverage"
                raise ValueError(msg)
            if state.decision_known_on > self.as_known_on or (
                state.release.as_known_at is not None
                and state.release.as_known_at > self.as_known_on
            ):
                msg = "Assignment or release was not known at the cutoff"
                raise ValueError(msg)
            for source in state.release.sources.records:
                if (
                    source.retrieved_at is not None
                    and source.retrieved_at.date() > self.as_known_on
                ):
                    msg = "Assignment source retrieval is after the knowledge cutoff"
                    raise ValueError(msg)
            identity = release_sha256(state.release)
            prior = releases.setdefault(state.release.release_id, identity)
            if prior != identity:
                msg = "Release identity reused with different content"
                raise ValueError(msg)
            previous = state
        return self


@dataclass(frozen=True)
class AssignmentCostRow:
    """One exact-hour slice retaining assignment, decision and condition lineage."""

    activity_id: str
    state_id: str
    decision_id: str
    release_id: str
    release_sha256: str
    starts_at: datetime
    ends_at: datetime | None
    condition_ids: tuple[str, ...]
    exact_hours: Fraction
    components: dict[str, Fraction]


@dataclass(frozen=True)
class AssignmentCost:
    """Exact nominal-hour valuation, separate from cash paid or entitlement proof."""

    method_id: Literal["declared_assignment_path_v1"]
    currency: Literal["AUD"]
    timeline: AssignmentTimeline
    timeline_sha256: str
    activities: tuple[Activity, ...]
    snapshot_at: datetime | None
    rows: tuple[AssignmentCostRow, ...]
    components: dict[str, Fraction]
    total: Fraction


def _validated(timeline: AssignmentTimeline) -> AssignmentTimeline:
    """Reject unchecked copies at every nested state, release and source level."""
    return AssignmentTimeline.model_validate(timeline.model_dump())


def _state_at(timeline: AssignmentTimeline, when: datetime) -> AssignmentState:
    """Select exactly one half-open state without carrying one across a gap."""
    for state in timeline.states:
        if state.starts_at <= when < state.ends_at:
            return state
    msg = "No assignment coverage for the requested instant"
    raise ValueError(msg)


def _result(
    timeline: AssignmentTimeline,
    activities: tuple[Activity, ...],
    rows: tuple[AssignmentCostRow, ...],
    snapshot_at: datetime | None,
) -> AssignmentCost:
    """Aggregate exact component amounts and bind the complete input timeline."""
    components: dict[str, Fraction] = {}
    for row in rows:
        for name, amount in row.components.items():
            components[name] = components.get(name, Fraction(0)) + amount
    encoded = json.dumps(
        timeline.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return AssignmentCost(
        method_id="declared_assignment_path_v1",
        currency="AUD",
        timeline=timeline,
        timeline_sha256=sha256(encoded).hexdigest(),
        activities=activities,
        snapshot_at=snapshot_at,
        rows=rows,
        components=dict(sorted(components.items())),
        total=sum(components.values(), Fraction(0)),
    )


def cost_assignment_snapshot(
    timeline: AssignmentTimeline,
    when: datetime,
    hours: Decimal,
) -> AssignmentCost:
    """Value explicit nominal hours in the state effective at an aware instant."""
    timeline = _validated(timeline)
    instant = _instant(when)
    quantity = SnapshotQuantity(hours=hours)
    state = _state_at(timeline, instant)
    day = instant.astimezone(ZoneInfo(state.timezone)).date()
    priced = cost_condition_snapshot(state.release, day, quantity.hours)
    exact_hours = Fraction(quantity.hours)
    row = AssignmentCostRow(
        activity_id="snapshot",
        state_id=state.state_id,
        decision_id=state.decision_id,
        release_id=state.release.release_id,
        release_sha256=release_sha256(state.release),
        starts_at=instant,
        ends_at=None,
        condition_ids=tuple(c.condition_id for c in priced.conditions),
        exact_hours=exact_hours,
        components={
            name: rate * exact_hours
            for name, rate in exact_hourly_components(state.release, day).items()
        },
    )
    return _result(timeline, (), (row,), instant)


def _activity_rows(
    state: AssignmentState,
    activity: Activity,
) -> tuple[AssignmentCostRow, ...]:
    """Reuse condition/calendar admission and retain unrounded rational amounts."""
    priced = cost_condition_activity(state.release, activity, state.timezone)
    identity = release_sha256(state.release)
    zone = ZoneInfo(state.timezone)
    rows: list[AssignmentCostRow] = []
    for segment in priced.segments:
        duration = segment.ends_at - segment.starts_at
        micros = (
            duration.days * 86400 + duration.seconds
        ) * 1000000 + duration.microseconds
        hours = Fraction(micros, 3600000000) * Fraction(activity.resources)
        rates = exact_hourly_components(
            state.release,
            segment.starts_at.astimezone(zone).date(),
        )
        rows.append(
            AssignmentCostRow(
                activity_id=activity.activity_id,
                state_id=state.state_id,
                decision_id=state.decision_id,
                release_id=state.release.release_id,
                release_sha256=identity,
                starts_at=segment.starts_at,
                ends_at=segment.ends_at,
                condition_ids=segment.condition_ids,
                exact_hours=hours,
                components={name: rate * hours for name, rate in rates.items()},
            ),
        )
    return tuple(rows)


def cost_assignment_activities(
    timeline: AssignmentTimeline,
    activities: tuple[Activity, ...],
) -> AssignmentCost:
    """Split one subject's nonoverlapping activities at assignment and day edges."""
    timeline = _validated(timeline)
    activities = tuple(Activity.model_validate(a.model_dump()) for a in activities)
    if not activities or len({a.activity_id for a in activities}) != len(activities):
        msg = "Assignment costing requires nonempty unique activities"
        raise ValueError(msg)
    ordered = tuple(
        sorted(
            activities,
            key=lambda a: (_instant(a.starts_at), a.activity_id),
        ),
    )
    previous_end: datetime | None = None
    rows: list[AssignmentCostRow] = []
    for activity in ordered:
        if activity.resource_id != timeline.subject_id or activity.resources > 1:
            msg = "Assignment activities require one matching subject/resource"
            raise ValueError(msg)
        cursor = _instant(activity.starts_at)
        end = _instant(activity.ends_at)
        if previous_end is not None and cursor < previous_end:
            msg = "Assignment activities overlap for the subject"
            raise ValueError(msg)
        previous_end = end
        while cursor < end:
            state = _state_at(timeline, cursor)
            stop = min(end, state.ends_at)
            clip = activity.model_copy(update={"starts_at": cursor, "ends_at": stop})
            rows.extend(_activity_rows(state, clip))
            cursor = stop
    return _result(timeline, ordered, tuple(rows), None)
