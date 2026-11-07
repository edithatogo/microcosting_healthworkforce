# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Explicit productive-capacity and incremental-cover scenario arithmetic."""

from decimal import Decimal
from fractions import Fraction
lazy from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from src.conditions import ConditionRelease, exact_hourly_components
lazy from src.unit_quotes import NonnegativeQuantity


class CapacityLoss(BaseModel):
    """An explicitly modelled, non-overlapping annual loss of productive hours."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    loss_id: str = Field(min_length=1)
    hours: NonnegativeQuantity


class CapacityScenarioInputs(BaseModel):
    """Analyst-supplied utilisation and incremental cover, not entitlements."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    losses: tuple[CapacityLoss, ...]
    cover_hours: Decimal = Field(ge=0, allow_inf_nan=False)
    cover_hourly_cost: Decimal = Field(ge=0, allow_inf_nan=False)
    losses_disjoint: bool


class CapacityScenarioResult(BaseModel):
    """An explicitly labelled scenario, with base and incremental costs separate."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    release_id: str
    method_id: str = "paid_capacity_scenario_v1"
    as_of: date
    paid_hours: Decimal
    productive_hours: Decimal
    paid_cost: Decimal
    incremental_cover_cost: Decimal
    total_cost: Decimal
    cost_per_productive_hour: Decimal
    exact_total_numerator: int
    exact_total_denominator: int = Field(gt=0)
    exact_productive_rate_numerator: int
    exact_productive_rate_denominator: int = Field(gt=0)
    condition_ids: tuple[str, ...]
    assumptions: CapacityScenarioInputs


def _as_decimal(value: Fraction) -> Decimal:
    """Convert an exact result once using the active decimal context."""
    return Decimal(value.numerator) / Decimal(value.denominator)


def capacity_scenario(
    release: ConditionRelease,
    when: date,
    inputs: CapacityScenarioInputs,
) -> CapacityScenarioResult:
    """Calculate an explicit scenario without treating leave as a cash saving.

    Losses are assumed to be distinct periods within paid hours; the caller must
    establish the loss amounts and cover cost independently. Cover is incremental.
    The productive-hours denominator refers only to the original worker; any
    productivity delivered by cover is outside this ratio.
    """
    release = ConditionRelease.model_validate(release.model_dump())
    inputs = CapacityScenarioInputs.model_validate_json(inputs.model_dump_json())
    if not inputs.losses_disjoint:
        msg = "Loss periods must be explicitly asserted disjoint"
        raise ValueError(msg)
    if len({item.loss_id for item in inputs.losses}) != len(inputs.losses):
        msg = "Duplicate capacity loss identity"
        raise ValueError(msg)
    rates = exact_hourly_components(release, when)
    current = [
        c for c in release.conditions if c.effective_from <= when < c.effective_to
    ]
    paid = next(c.value for c in current if c.kind == "paid_hours")
    loss_hours = sum(
        (Fraction(loss.hours) for loss in inputs.losses),
        Fraction(0),
    )
    exact_productive = Fraction(paid) - loss_hours
    if exact_productive <= 0:
        msg = "Scenario must retain positive productive hours"
        raise ValueError(msg)
    if Fraction(inputs.cover_hours) > loss_hours:
        msg = "Incremental cover cannot exceed specified lost hours"
        raise ValueError(msg)
    paid_cost = sum(rates.values(), Fraction(0)) * Fraction(paid)
    cover_cost = Fraction(inputs.cover_hours) * Fraction(inputs.cover_hourly_cost)
    exact_total = paid_cost + cover_cost
    exact_rate = exact_total / exact_productive
    return CapacityScenarioResult(
        release_id=release.release_id,
        as_of=when,
        paid_hours=paid,
        productive_hours=_as_decimal(exact_productive),
        paid_cost=_as_decimal(paid_cost),
        incremental_cover_cost=_as_decimal(cover_cost),
        total_cost=_as_decimal(exact_total),
        cost_per_productive_hour=_as_decimal(exact_rate),
        exact_total_numerator=exact_total.numerator,
        exact_total_denominator=exact_total.denominator,
        exact_productive_rate_numerator=exact_rate.numerator,
        exact_productive_rate_denominator=exact_rate.denominator,
        condition_ids=tuple(c.condition_id for c in current),
        assumptions=inputs,
    )
