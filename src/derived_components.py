# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Explicit ordered additive component dependencies for condition costing."""

from dataclasses import dataclass
from fractions import Fraction
from typing import Self
from zoneinfo import ZoneInfo
lazy from datetime import date
lazy from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.conditions import (
    ConditionCostResult,
    ConditionRelease,
    ConditionSnapshotResult,
    cost_condition_activity,
    cost_condition_snapshot,
    exact_hourly_components,
)
from src.costing import Activity
lazy from src.pay_period_effective import RetrospectiveAuthority


class DerivedComponentRule(BaseModel):
    """A reviewed fraction of named earlier base or derived components."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    rule_id: str = Field(min_length=1)
    component: str = Field(min_length=1)
    bases: tuple[str, ...] = Field(min_length=1)
    fraction: Decimal = Field(ge=0, allow_inf_nan=False)
    source_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation: str = Field(min_length=1)
    effective_from: date
    effective_to: date
    reviewed: bool
    retrospective: RetrospectiveAuthority | None = None

    @model_validator(mode="after")
    def valid_rule(self) -> Self:
        """Require reviewed evidence, a bounded date and distinct named bases."""
        if (
            not self.reviewed
            or not self.citation.strip()
            or self.effective_to <= self.effective_from
            or not self.component.strip()
            or any(not name.strip() for name in self.bases)
            or len(set(self.bases)) != len(self.bases)
        ):
            msg = "Derived rule requires reviewed scope, dates and unique bases"
            raise ValueError(msg)
        return self


@dataclass(frozen=True)
class DerivedRow:
    """An auditable additive cost for one rule and one dated segment."""

    day: date
    rule: DerivedComponentRule
    base_hourly: Fraction
    hourly_amount: Fraction
    quantity_hours: Fraction
    amount: Fraction


@dataclass(frozen=True)
class DerivedCost:
    """Preserve the base ledger, additive rows and exact combined total."""

    base: ConditionSnapshotResult | ConditionCostResult
    rows: tuple[DerivedRow, ...]
    exact_total: Fraction


def _rows(
    release: ConditionRelease,
    rules: tuple[DerivedComponentRule, ...],
    when: date,
    quantity: Fraction,
) -> tuple[DerivedRow, ...]:
    rates = exact_hourly_components(release, when)
    included = {
        name
        for item in release.conditions
        if item.kind == "salary" and item.effective_from <= when < item.effective_to
        for name in item.included_components
    }
    result: list[DerivedRow] = []
    seen: set[str] = set()
    for raw in rules:
        rule = DerivedComponentRule.model_validate(raw.model_dump())
        if rule.component in included:
            msg = "Derived component duplicates a salary inclusion"
            raise ValueError(msg)
        if rule.rule_id in seen or rule.component in rates:
            msg = "Derived rule identities and component names must be unique"
            raise ValueError(msg)
        seen.add(rule.rule_id)
        if not rule.effective_from <= when < rule.effective_to:
            msg = "Derived rule does not cover costing date"
            raise ValueError(msg)
        _require_rule_source(release, rule, when)
        if any(name not in rates for name in rule.bases):
            msg = "Derived rule base is missing or not yet defined"
            raise ValueError(msg)
        base = sum((rates[name] for name in rule.bases), Fraction(0))
        hourly = base * Fraction(rule.fraction)
        rates[rule.component] = hourly
        result.append(DerivedRow(when, rule, base, hourly, quantity, hourly * quantity))
    return tuple(result)


def _require_rule_source(
    release: ConditionRelease,
    rule: DerivedComponentRule,
    when: date,
) -> None:
    """Qualify source scope and any separately reviewed retrospective date."""
    authority = rule.retrospective
    dates = (when,)
    if authority is not None:
        if release.as_known_at is None or authority.as_known_at != release.as_known_at:
            msg = "Derived retrospective rule requires the release knowledge date"
            raise ValueError(msg)
        dates += (authority.known_from, authority.as_known_at)
    for day in dates:
        if authority is not None and day < authority.known_from:
            if not authority.entitlement_from <= day < authority.entitlement_to:
                msg = "Date outside derived retrospective entitlement interval"
                raise ValueError(msg)
            continue
        source = release.sources.require_applicable(
            rule.source_id,
            day,
            release.jurisdiction,
            release.employer,
            release.classification,
        )
        if source.sha256 != rule.source_sha256:
            msg = "Derived rule source hash mismatch"
            raise ValueError(msg)


def cost_derived_snapshot(
    release: ConditionRelease,
    when: date,
    hours: Decimal,
    rules: tuple[DerivedComponentRule, ...],
) -> DerivedCost:
    """Add explicit dependencies to one nominal paid-hours snapshot."""
    release = ConditionRelease.model_validate(release.model_dump())
    base = cost_condition_snapshot(release, when, hours)
    rows = _rows(release, rules, when, Fraction(hours))
    exact_base = Fraction(base.exact_total_numerator, base.exact_total_denominator)
    return DerivedCost(
        base,
        rows,
        exact_base + sum((row.amount for row in rows), Fraction(0)),
    )


def cost_derived_activity(
    release: ConditionRelease,
    activity: Activity,
    timezone: str,
    rules: tuple[DerivedComponentRule, ...],
) -> DerivedCost:
    """Apply the same explicit dependencies to each dated activity segment."""
    release = ConditionRelease.model_validate(release.model_dump())
    activity = Activity.model_validate(activity.model_dump())
    base = cost_condition_activity(release, activity, timezone)
    zone = ZoneInfo(timezone)
    rows: list[DerivedRow] = []
    for segment in base.segments:
        elapsed = segment.ends_at - segment.starts_at
        micros = (
            elapsed.days * 86400 + elapsed.seconds
        ) * 1000000 + elapsed.microseconds
        hours = Fraction(micros, 3600000000) * Fraction(activity.resources)
        rows.extend(
            _rows(release, rules, segment.starts_at.astimezone(zone).date(), hours),
        )
    exact_base = Fraction(base.exact_total_numerator, base.exact_total_denominator)
    return DerivedCost(
        base,
        tuple(rows),
        exact_base + sum((row.amount for row in rows), Fraction(0)),
    )
