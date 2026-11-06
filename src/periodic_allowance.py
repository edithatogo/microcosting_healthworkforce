# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Explicit periodic allocation of an accepted annual allowance."""

from dataclasses import dataclass
from fractions import Fraction
from typing import Self
lazy from datetime import date
lazy from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.condition_history import release_sha256
from src.conditions import Condition, ConditionRelease


class AllowancePortion(BaseModel):
    """Caller-classified hours and independent accrual and payment factors."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    label: str = Field(min_length=1)
    hours: Decimal = Field(ge=0, allow_inf_nan=False)
    accrual_factor: Decimal = Field(ge=0, le=1, allow_inf_nan=False)
    payment_factor: Decimal = Field(ge=0, le=1, allow_inf_nan=False)

    @model_validator(mode="after")
    def nonblank_label(self) -> Self:
        """Require explicit classification without prescribing its meaning."""
        if not self.label.strip():
            msg = "Allowance portion requires a label"
            raise ValueError(msg)
        return self


class AllowancePeriod(BaseModel):
    """Caller-supplied half-open payroll period and full-time assumptions."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    starts_on: date
    ends_on: date
    full_time_hours: Decimal = Field(gt=0, allow_inf_nan=False)
    periods_per_year: Decimal = Field(gt=0, allow_inf_nan=False)
    portions: tuple[AllowancePortion, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_period(self) -> Self:
        """Reject invalid periods and excessive allocations."""
        if self.ends_on <= self.starts_on:
            msg = "Allowance period must be nonempty"
            raise ValueError(msg)
        if len({part.label for part in self.portions}) != len(self.portions):
            msg = "Allowance portion labels must be unique"
            raise ValueError(msg)
        if sum(
            (Fraction(part.hours) for part in self.portions),
            Fraction(0),
        ) > Fraction(self.full_time_hours):
            msg = "Allowance hours exceed specified full-time hours"
            raise ValueError(msg)
        return self


@dataclass(frozen=True)
class AllowancePortionCost:
    """Exact accrual and payment for an explicitly classified portion."""

    portion: AllowancePortion
    accrued: Fraction
    payable: Fraction


@dataclass(frozen=True)
class PeriodicAllowanceCost:
    """Separate exact accrual and payment; no implicit ledger combination."""

    release_id: str
    release_sha256: str
    condition: Condition
    period: AllowancePeriod
    portions: tuple[AllowancePortionCost, ...]
    accrued: Fraction
    payable: Fraction


def cost_periodic_allowance(
    release: ConditionRelease,
    component: str,
    period: AllowancePeriod,
) -> PeriodicAllowanceCost:
    """Allocate a full-time annual amount using caller-reviewed period inputs.

    No award selection, eligibility, payroll calendar, rounding or leave policy
    is inferred. A change within the period requires explicit splitting. This
    result must not be added to an hourly ledger already containing the same
    fixed annual condition.
    """
    release = ConditionRelease.model_validate(release.model_dump())
    period = AllowancePeriod.model_validate(period.model_dump())
    candidates = [
        c
        for c in release.conditions
        if c.kind == "fixed_annual"
        and c.component == component
        and c.effective_from <= period.starts_on
        and period.ends_on <= c.effective_to
    ]
    if len(candidates) != 1:
        msg = "Exactly one accepted annual allowance must cover the whole period"
        raise ValueError(msg)
    selected = candidates[0]
    unit = (
        Fraction(selected.value)
        / Fraction(period.periods_per_year)
        / Fraction(period.full_time_hours)
    )
    rows = tuple(
        AllowancePortionCost(
            portion=part,
            accrued=unit * Fraction(part.hours) * Fraction(part.accrual_factor),
            payable=unit * Fraction(part.hours) * Fraction(part.payment_factor),
        )
        for part in period.portions
    )
    return PeriodicAllowanceCost(
        release.release_id,
        release_sha256(release),
        selected,
        period,
        rows,
        sum((row.accrued for row in rows), Fraction(0)),
        sum((row.payable for row in rows), Fraction(0)),
    )
