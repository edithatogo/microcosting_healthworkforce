# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Exact whole-period comparisons of explicitly scoped contribution alternatives."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from fractions import Fraction
from typing import Literal, Self
from zoneinfo import ZoneInfo

from pydantic import Field, model_validator

from src.costing import (
    Activity,
    CostRelease,
    CostResult,
    FrozenModel,
    ResourceUse,
    cost_dynamic,
    cost_static,
)


def _utc(value: datetime) -> datetime:
    if value.utcoffset() is None:
        msg = "Contribution times must be timezone aware"
        raise ValueError(msg)
    return value.astimezone(UTC)


def _micros(value: timedelta) -> int:
    return (value.days * 86400 + value.seconds) * 1000000 + value.microseconds


class ContributionPeriod(FrozenModel):
    """One employee/resource period with explicitly complete relevant earnings."""

    period_id: str = Field(min_length=1)
    resource_id: str = Field(min_length=1)
    allocation_id: str = Field(min_length=1)
    starts_at: datetime
    ends_at: datetime
    earnings_complete: bool

    @model_validator(mode="after")
    def valid_period(self) -> Self:
        """Missing history and impossible intervals are not zero earnings."""
        if not self.earnings_complete:
            msg = "Complete relevant period earnings must be explicitly asserted"
            raise ValueError(msg)
        if _utc(self.ends_at) <= _utc(self.starts_at) or any(
            not value.strip()
            for value in (self.period_id, self.resource_id, self.allocation_id)
        ):
            msg = "Contribution period needs nonblank identities and positive duration"
            raise ValueError(msg)
        return self


class ContributionFactor(FrozenModel):
    """A reviewed fraction with its own source and bounded operative instants."""

    factor_id: str = Field(min_length=1)
    fraction: Decimal = Field(ge=0, allow_inf_nan=False)
    starts_at: datetime
    ends_at: datetime
    source_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation: str = Field(min_length=1)
    reviewed: bool

    @model_validator(mode="after")
    def valid_factor(self) -> Self:
        """Require review, a citation and a positive aware interval."""
        if (
            not self.reviewed
            or not self.factor_id.strip()
            or not self.citation.strip()
            or _utc(self.ends_at) <= _utc(self.starts_at)
        ):
            msg = "Contribution factor requires review, citation and valid dates"
            raise ValueError(msg)
        return self


class ContributionCap(FrozenModel):
    """Reviewed earnings ceiling and verified prior usage in its window."""

    limit: Decimal = Field(gt=0, allow_inf_nan=False)
    prior_eligible_earnings: Decimal = Field(ge=0, allow_inf_nan=False)
    starts_at: datetime
    ends_at: datetime
    history_through: datetime
    source_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation: str = Field(min_length=1)
    reviewed: bool

    @model_validator(mode="after")
    def valid_history(self) -> Self:
        """Require an explicit cutoff inside the reviewed cap window."""
        start = _utc(self.starts_at)
        cutoff = _utc(self.history_through)
        if (
            not self.reviewed
            or not self.citation.strip()
            or not start <= cutoff < _utc(self.ends_at)
            or (start == cutoff and self.prior_eligible_earnings != 0)
        ):
            msg = (
                "Contribution cap requires reviewed dates and consistent prior earnings"
            )
            raise ValueError(msg)
        return self


class ContributionAlternative(FrozenModel):
    """One independent base definition and effective-dated factor schedule."""

    alternative_id: str = Field(min_length=1)
    bases: tuple[str, ...] = Field(min_length=1)
    factors: tuple[ContributionFactor, ...] = Field(min_length=1)
    cap: ContributionCap | None = None

    @model_validator(mode="after")
    def valid_alternative(self) -> Self:
        """Reject duplicate bases/identities and overlapping factor schedules."""
        if (
            not self.alternative_id.strip()
            or len(set(self.bases)) != len(self.bases)
            or any(not name.strip() for name in self.bases)
            or len({f.factor_id for f in self.factors}) != len(self.factors)
        ):
            msg = "Contribution alternative needs unique nonblank bases and factors"
            raise ValueError(msg)
        previous: datetime | None = None
        for factor in sorted(self.factors, key=lambda f: _utc(f.starts_at)):
            if previous is not None and _utc(factor.starts_at) < previous:
                msg = "Contribution factor schedules overlap"
                raise ValueError(msg)
            previous = _utc(factor.ends_at)
        return self


class ContributionRule(FrozenModel):
    """Select one maximum after each alternative is summed over the whole period."""

    rule_id: str = Field(min_length=1)
    component: str = Field(min_length=1)
    alternatives: tuple[ContributionAlternative, ...] = Field(min_length=2)
    source_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation: str = Field(min_length=1)
    effective_from: date
    effective_to: date
    reviewed: bool
    local_timezone: str
    required_capabilities: tuple[str, ...] = ()

    @model_validator(mode="after")
    def valid_rule(self) -> Self:
        """Require reviewed comparison scope without guessing extra capabilities."""
        ZoneInfo(self.local_timezone)
        if (
            not self.reviewed
            or not self.rule_id.strip()
            or not self.component.strip()
            or not self.citation.strip()
            or self.effective_to <= self.effective_from
        ):
            msg = "Contribution rule requires review, citation and valid dates"
            raise ValueError(msg)
        if self.required_capabilities:
            msg = f"Unsupported contribution capabilities: {self.required_capabilities}"
            raise ValueError(msg)
        if len({a.alternative_id for a in self.alternatives}) != len(self.alternatives):
            msg = "Contribution alternatives require unique identities"
            raise ValueError(msg)
        if any(self.component in a.bases for a in self.alternatives):
            msg = "Contribution output component cannot be a base"
            raise ValueError(msg)
        return self


@dataclass(frozen=True)
class ContributionRow:
    """One exact candidate amount, linked to its factor and wage ledger row."""

    alternative_id: str
    factor: ContributionFactor
    activity_id: str
    rate_id: str
    starts_at: datetime
    ends_at: datetime | None
    bases: tuple[str, ...]
    base_amount: Fraction
    amount: Fraction
    eligible_base_amount: Fraction | None = None


@dataclass(frozen=True)
class ContributionTotal:
    """Retain each alternative's period total, including ties and losing amounts."""

    alternative_id: str
    amount: Fraction


@dataclass(frozen=True)
class PeriodContributionCost:
    """Preserve period, comparison/factor evidence and the unchanged base ledger."""

    method_id: Literal["aggregate_then_greater_total_v1"]
    mode: Literal["static_assumed_quantity", "dynamic_earned_activities"]
    period: ContributionPeriod
    rule: ContributionRule
    base: CostResult
    rows: tuple[ContributionRow, ...]
    alternatives: tuple[ContributionTotal, ...]
    winning_alternative_ids: tuple[str, ...]
    contribution: Fraction
    exact_total: Fraction


def _pieces(
    alternative: ContributionAlternative,
    start: datetime,
    end: datetime,
) -> tuple[tuple[datetime, datetime, ContributionFactor], ...]:
    pieces: list[tuple[datetime, datetime, ContributionFactor]] = []
    cursor = start
    for factor in sorted(alternative.factors, key=lambda f: _utc(f.starts_at)):
        left, right = max(start, _utc(factor.starts_at)), min(end, _utc(factor.ends_at))
        if left >= right:
            continue
        if left != cursor:
            msg = "Incomplete contribution factor coverage"
            raise ValueError(msg)
        pieces.append((left, right, factor))
        cursor = right
    if cursor != end:
        msg = "Incomplete contribution factor coverage"
        raise ValueError(msg)
    return tuple(pieces)


def _require_source(
    release: CostRelease,
    evidence: ContributionRule | ContributionFactor | ContributionCap,
    interval: tuple[datetime, datetime],
    scope: tuple[str, str, str],
    zone: ZoneInfo,
) -> None:
    for instant in (interval[0], interval[1] - timedelta(microseconds=1)):
        source = release.sources.require_applicable(
            evidence.source_id,
            instant.astimezone(zone).date(),
            *scope,
        )
        if source.sha256 != evidence.source_sha256:
            msg = "Contribution source hash mismatch"
            raise ValueError(msg)


def _prepare(
    release: CostRelease,
    period: ContributionPeriod,
    rule: ContributionRule,
) -> tuple[CostRelease, ContributionPeriod, ContributionRule]:
    release = CostRelease.model_validate(release.model_dump())
    period = ContributionPeriod.model_validate(period.model_dump())
    rule = ContributionRule.model_validate(rule.model_dump())
    start, end = _utc(period.starts_at), _utc(period.ends_at)
    rates = [
        r
        for r in release.rates
        if r.resource_id == period.resource_id
        and r.starts_at < end
        and (r.ends_at is None or r.ends_at > start)
    ]
    if not rates:
        msg = "No resource rate scope for contribution period"
        raise ValueError(msg)
    required = {name for a in rule.alternatives for name in a.bases}
    if any(required - r.components.keys() for r in rates):
        msg = "Contribution base component is missing; supply explicit zeros if known"
        raise ValueError(msg)
    if any(rule.component in r.components for r in rates):
        msg = "Contribution component is already included in the base release"
        raise ValueError(msg)
    zone = ZoneInfo(rule.local_timezone)
    if (
        start.astimezone(zone).date() < rule.effective_from
        or (end - timedelta(microseconds=1)).astimezone(zone).date()
        >= rule.effective_to
    ):
        msg = "Contribution rule dates do not cover the whole period"
        raise ValueError(msg)
    scope = (rates[0].jurisdiction, rates[0].employer, rates[0].classification)
    _require_source(release, rule, (start, end), scope, zone)
    for alternative in rule.alternatives:
        cap = alternative.cap
        if cap is not None:
            if _utc(cap.history_through) != start or end > _utc(cap.ends_at):
                msg = "Contribution cap must cover the period from its history cutoff"
                raise ValueError(msg)
            _require_source(
                release,
                cap,
                (_utc(cap.starts_at), _utc(cap.ends_at)),
                scope,
                zone,
            )
        for left, right, factor in _pieces(alternative, start, end):
            _require_source(release, factor, (left, right), scope, zone)
    return release, period, rule


def _calculate(
    release: CostRelease,
    period: ContributionPeriod,
    rule: ContributionRule,
    base: CostResult,
    mode: Literal["static_assumed_quantity", "dynamic_earned_activities"],
) -> PeriodContributionCost:
    rates = {r.rate_id: r for r in release.rates}
    rows: list[ContributionRow] = []
    totals: list[ContributionTotal] = []
    for alternative in sorted(rule.alternatives, key=lambda a: a.alternative_id):
        pieces = _pieces(alternative, _utc(period.starts_at), _utc(period.ends_at))
        if mode == "static_assumed_quantity" and len(pieces) != 1:
            msg = (
                "Static contribution quantity requires a single factor per alternative"
            )
            raise ValueError(msg)
        total = Fraction(0)
        cap = alternative.cap
        remaining = (
            max(
                Fraction(0),
                Fraction(cap.limit) - Fraction(cap.prior_eligible_earnings),
            )
            if cap is not None
            else None
        )
        for row in base.rows:
            hours = Fraction(row.exact_hours_numerator, row.exact_hours_denominator)
            hourly_base = sum(
                (
                    Fraction(rates[row.rate_id].components[name])
                    for name in alternative.bases
                ),
                Fraction(0),
            )
            for left, right, factor in pieces:
                start, stop = row.starts_at, row.ends_at
                quantity = hours
                if stop is not None:
                    duration = _micros(_utc(stop) - _utc(start))
                    start, stop = max(_utc(start), left), min(_utc(stop), right)
                    if start >= stop:
                        continue
                    quantity *= Fraction(
                        _micros(stop - start),
                        duration,
                    )
                amount_base = hourly_base * quantity
                eligible_base = amount_base
                if remaining is not None:
                    if amount_base < 0:
                        msg = "Capped contributions require nonnegative earnings"
                        raise ValueError(msg)
                    eligible_base = min(amount_base, remaining)
                    remaining -= eligible_base
                amount = eligible_base * Fraction(factor.fraction)
                rows.append(
                    ContributionRow(
                        alternative.alternative_id,
                        factor,
                        row.activity_id,
                        row.rate_id,
                        start,
                        stop,
                        alternative.bases,
                        amount_base,
                        amount,
                        eligible_base if cap is not None else None,
                    ),
                )
                total += amount
        totals.append(ContributionTotal(alternative.alternative_id, total))
    selected = max(t.amount for t in totals)
    winners = tuple(t.alternative_id for t in totals if t.amount == selected)
    return PeriodContributionCost(
        "aggregate_then_greater_total_v1",
        mode,
        period,
        rule,
        base,
        tuple(rows),
        tuple(totals),
        winners,
        selected,
        Fraction(base.exact_total_numerator, base.exact_total_denominator) + selected,
    )


def cost_contribution_activities(
    release: CostRelease,
    period: ContributionPeriod,
    rule: ContributionRule,
    activities: tuple[Activity, ...],
) -> PeriodContributionCost:
    """Compare complete earned-activity alternatives once, never per segment.

    One resource category and one physical allocation are required. Wage and
    factor changes split candidate rows before each alternative's total is summed.
    Payment dates and statutory base selection are supplied outside this calculation.
    """
    release, period, rule = _prepare(release, period, rule)
    activities = tuple(Activity.model_validate(a.model_dump()) for a in activities)
    for activity in activities:
        if (
            activity.resource_id != period.resource_id
            or activity.allocation_id != period.allocation_id
            or activity.resources != Decimal(1)
        ):
            msg = "Contribution requires one resource and matching allocation"
            raise ValueError(msg)
        if _utc(activity.starts_at) < _utc(period.starts_at) or _utc(
            activity.ends_at,
        ) > _utc(period.ends_at):
            msg = "Earning activity lies outside contribution period"
            raise ValueError(msg)
    ordered = tuple(sorted(activities, key=lambda a: _utc(a.starts_at)))
    return _calculate(
        release,
        period,
        rule,
        cost_dynamic(release, ordered),
        "dynamic_earned_activities",
    )


def cost_contribution_snapshot(
    release: CostRelease,
    period: ContributionPeriod,
    rule: ContributionRule,
    at: datetime,
    resource: ResourceUse,
) -> PeriodContributionCost:
    """Compare an explicit complete quantity at one assumed snapshot price.

    This is a constant-price quantity scenario, not earned/payment history.
    Each alternative needs one factor covering the entire declared period.
    """
    release, period, rule = _prepare(release, period, rule)
    resource = ResourceUse.model_validate(resource.model_dump())
    if (
        resource.resource_id != period.resource_id
        or not _utc(period.starts_at) <= _utc(at) < _utc(period.ends_at)
        or Fraction(resource.hours)
        > Fraction(_micros(_utc(period.ends_at) - _utc(period.starts_at)), 3600000000)
    ):
        msg = "Static quantity, resource or snapshot does not match contribution period"
        raise ValueError(msg)
    return _calculate(
        release,
        period,
        rule,
        cost_static(release, at, (resource,)),
        "static_assumed_quantity",
    )
