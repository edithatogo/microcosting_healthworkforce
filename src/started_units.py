# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Exact started-unit quantities for explicitly reviewed exposure groups."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from itertools import pairwise
from typing import Literal, Self
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, field_validator, model_validator

from src.unit_quotes import (
    QuoteModel,
    QuoteQuantity,
    UnitQuoteRelease,
    UnitQuoteResult,
    price_units,
)


def _micros(value: timedelta) -> int:
    return (value.days * 86400 + value.seconds) * 1000000 + value.microseconds


class StartedUnitRule(QuoteModel):
    """Explicit quantum, grouping and elapsed-time interpretation with source scope."""

    rule_id: str
    component: str
    unit: str
    quantum: timedelta
    method: Literal["ceil_grouped_elapsed_units_v1"]
    grouping_basis: str
    interpretation_kind: Literal["source_reviewed", "analyst_assumption"]
    interpretation_basis: str
    local_timezone: str
    source_id: str
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation: str
    reviewed: bool
    effective_from: date
    effective_to: date
    as_known_on: date
    jurisdiction: str
    employer: str
    classification: str

    @model_validator(mode="after")
    def valid_rule(self) -> Self:
        """Reject an unreviewed grouping or an empty quantum/operative interval."""
        try:
            ZoneInfo(self.local_timezone)
        except ZoneInfoNotFoundError as error:
            msg = "Started-unit policy requires a known timezone"
            raise ValueError(msg) from error
        if (
            not self.reviewed
            or _micros(self.quantum) <= 0
            or (self.effective_to <= self.effective_from)
        ):
            msg = "Started-unit rule requires review, positive quantum and valid dates"
            raise ValueError(msg)
        return self


class TimedExposure(QuoteModel):
    """A positive aware interval with UTC ordering, without inferred paid hours."""

    starts_at: datetime
    ends_at: datetime

    @field_validator("starts_at", "ends_at")
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        """Normalize instants before interval arithmetic or containment checks."""
        if value.utcoffset() is None:
            msg = "Exposure times must be timezone aware"
            raise ValueError(msg)
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def positive(self) -> Self:
        """Reject zero/negative intervals instead of converting them into use."""
        if self.starts_at.utcoffset() is None or self.ends_at.utcoffset() is None:
            msg = "Exposure times must be timezone aware"
            raise ValueError(msg)
        if self.ends_at.astimezone(UTC) <= self.starts_at.astimezone(UTC):
            msg = "Exposure interval must be positive"
            raise ValueError(msg)
        return self


class ExposureInterval(TimedExposure):
    """One actually declared interval within the reviewed aggregation group."""

    interval_id: str


class StartedUnitWindow(TimedExposure):
    """A complete group with an explicit negative fact when no exposure occurred."""

    window_id: str
    resource_id: str
    valued_on: date
    quote_id: str
    intervals: tuple[ExposureInterval, ...]
    no_exposure_confirmed: bool
    eligibility_verified: bool
    history_complete: bool
    input_kind: Literal["observed_case_evidence", "analyst_assumption"]
    basis: str
    evidence_id: str
    evidence_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    known_on: date

    @model_validator(mode="after")
    def complete_history(self) -> Self:
        """Require qualified history and consistent positive or negative use."""
        if (
            not self.eligibility_verified
            or not self.history_complete
            or self.no_exposure_confirmed != (not self.intervals)
        ):
            msg = (
                "Require complete eligible history "
                "and explicit consistent exposure fact"
            )
            raise ValueError(msg)
        return self


@dataclass(frozen=True)
class StartedUnitQuantity:
    """Keep physical exposure, rounded paid units and additional time separate."""

    window: StartedUnitWindow
    exposure_microseconds: int
    quantum_microseconds: int
    payable_units: int

    @property
    def paid_quantum_microseconds(self) -> int:
        """Return paid quantum size without inventing additional worked intervals."""
        return self.payable_units * self.quantum_microseconds

    @property
    def rounding_increment_microseconds(self) -> int:
        """Retain the positive ceiling adjustment without calling it exposure."""
        return self.paid_quantum_microseconds - self.exposure_microseconds


@dataclass(frozen=True)
class StartedUnitResult:
    """Source-qualified quantities and exact prices with explicit scenario status."""

    rule: StartedUnitRule
    quantities: tuple[StartedUnitQuantity, ...]
    scenario: bool
    prices: UnitQuoteResult


def price_started_units(
    rule: StartedUnitRule,
    release: UnitQuoteRelease,
    windows: tuple[StartedUnitWindow, ...],
) -> StartedUnitResult:
    """Sum non-overlapping exposure intervals and ceiling once per reviewed group.

    The declared quantum produces one named price unit. Grouping, elapsed-time
    interpretation and eligibility are upstream reviewed facts or assumptions.
    No per-fragment rounding, elapsed gap payment, roster-hour conversion, rolling
    cap or mixed-price-group allocation is inferred.
    """
    rule = StartedUnitRule.model_validate(dict(rule))
    release = UnitQuoteRelease.model_validate(release.model_dump())
    windows = tuple(
        StartedUnitWindow.model_validate(
            dict(w)
            | {
                "intervals": tuple(
                    ExposureInterval.model_validate(dict(i)) for i in w.intervals
                ),
            },
        )
        for w in windows
    )
    if (rule.jurisdiction, rule.employer, rule.classification, rule.as_known_on) != (
        release.jurisdiction,
        release.employer,
        release.classification,
        release.as_known_on,
    ):
        msg = "Started-unit policy/prices require matching scope and knowledge date"
        raise ValueError(msg)
    if not windows or len({w.window_id for w in windows}) != len(windows):
        msg = "Require nonempty uniquely identified windows"
        raise ValueError(msg)
    ordered = tuple(sorted(windows, key=lambda w: (w.resource_id, w.starts_at)))
    if any(
        a.resource_id == b.resource_id and b.starts_at < a.ends_at
        for a, b in pairwise(ordered)
    ):
        msg = "Started-unit windows overlap for the same resource"
        raise ValueError(msg)
    zone = ZoneInfo(rule.local_timezone)
    quotes = {q.quote_id: q for q in release.quotes}
    quantities: list[StartedUnitQuantity] = []
    priced: list[QuoteQuantity] = []
    quantum = _micros(rule.quantum)
    scenario = rule.interpretation_kind == "analyst_assumption"
    for window in ordered:
        first = window.starts_at.astimezone(zone).date()
        last = (window.ends_at - timedelta(microseconds=1)).astimezone(zone).date()
        if (
            not rule.effective_from <= first <= window.valued_on <= last
            or last >= rule.effective_to
            or window.known_on > rule.as_known_on
            or (
                window.input_kind == "observed_case_evidence" and last > window.known_on
            )
        ):
            msg = "Window dates/evidence exceed policy or knowledge coverage"
            raise ValueError(msg)
        for day in (first, last):
            source = release.sources.require_applicable(
                rule.source_id,
                day,
                rule.jurisdiction,
                rule.employer,
                rule.classification,
            )
            if (
                source.sha256 != rule.source_sha256
                or source.retrieved_at is None
                or (source.retrieved_at.date() > rule.as_known_on)
            ):
                msg = "Started-unit policy requires matching held hash and known source"
                raise ValueError(msg)
        quote = quotes.get(window.quote_id)
        if (
            quote is None
            or quote.component != rule.component
            or quote.unit != rule.unit
            or (not quote.starts_on <= first <= last < quote.ends_on)
        ):
            msg = "Selected quote must match component/unit and cover the whole group"
            raise ValueError(msg)
        intervals = tuple(sorted(window.intervals, key=lambda i: i.starts_at))
        if (
            len({i.interval_id for i in intervals}) != len(intervals)
            or any(
                not window.starts_at <= i.starts_at < i.ends_at <= window.ends_at
                for i in intervals
            )
            or any(b.starts_at < a.ends_at for a, b in pairwise(intervals))
        ):
            msg = "Exposure intervals require unique IDs, containment and no overlap"
            raise ValueError(msg)
        elapsed = sum(_micros(i.ends_at - i.starts_at) for i in intervals)
        units = (elapsed + quantum - 1) // quantum
        quantities.append(StartedUnitQuantity(window, elapsed, quantum, units))
        assumed = rule.interpretation_kind == "analyst_assumption" or (
            window.input_kind == "analyst_assumption"
        )
        scenario |= assumed
        priced.append(
            QuoteQuantity(
                quantity_id=window.window_id,
                quote_id=window.quote_id,
                unit=rule.unit,
                quantity=Decimal(units),
                valued_on=window.valued_on,
                quantity_kind="analyst_assumption" if assumed else "observed_use",
                basis=window.basis,
            ),
        )
    return StartedUnitResult(
        rule,
        tuple(quantities),
        scenario,
        price_units(release, tuple(priced)),
    )
