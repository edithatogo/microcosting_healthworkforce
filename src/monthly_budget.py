# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Explicit calendar-month salary budgeting, separate from roster payroll."""

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
from fractions import Fraction
from itertools import pairwise
from typing import Self
lazy from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MonthlySalaryRate(BaseModel):
    """Analyst-supplied annual salary over a bounded period, end exclusive."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    rate_id: str = Field(min_length=1)
    effective_from: date
    effective_to: date
    annual_salary: Decimal = Field(ge=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_period(self) -> Self:
        """Require bounded salary rates."""
        if not self.rate_id.strip() or self.effective_to <= self.effective_from:
            msg = "Rate periods must be nonempty"
            raise ValueError(msg)
        return self


@dataclass(frozen=True)
class MonthlyBudgetRow:
    """A month/rate segment with its exact salary and calendar-day count."""

    month: date
    rate: MonthlySalaryRate
    covered_days: int
    days_in_month: int
    amount: Fraction


@dataclass(frozen=True)
class MonthlyBudget:
    """Unrounded scenario total and auditable monthly rows."""

    method_id: str
    start: date
    end_inclusive: date
    fte: Decimal
    rows: tuple[MonthlyBudgetRow, ...]
    total: Fraction


def _next_month(month: date) -> date:
    months_per_year = 12
    return date(
        month.year + (month.month == months_per_year),
        month.month % months_per_year + 1,
        1,
    )


def _month_rows(
    month: date,
    first: date,
    last: date,
    fte: Decimal,
    rates: list[MonthlySalaryRate],
) -> tuple[MonthlyBudgetRow, ...]:
    """Intersect the covered month with disjoint rate periods."""
    days = monthrange(month.year, month.month)[1]
    rows: list[MonthlyBudgetRow] = []
    for rate in rates:
        segment_start = max(first, rate.effective_from)
        if segment_start > last or segment_start >= rate.effective_to:
            continue
        segment_end = min(last, rate.effective_to - timedelta(days=1))
        covered = (segment_end - segment_start).days + 1
        amount = Fraction(rate.annual_salary) * Fraction(fte) * covered / (12 * days)
        rows.append(MonthlyBudgetRow(month, rate, covered, days, amount))
    if sum(row.covered_days for row in rows) != (last - first).days + 1:
        msg = "Monthly salary rate is missing for a costing day"
        raise ValueError(msg)
    return tuple(rows)


def monthly_salary_budget(
    start: date,
    end_inclusive: date,
    fte: Decimal,
    rates: tuple[MonthlySalaryRate, ...],
) -> MonthlyBudget:
    """Prorate annual salary/12 by inclusive days in each calendar month.

    Rates are explicit dated inputs; no rounding, award, leave, on-cost or
    worker eligibility is inferred. This scenario is not elapsed-hour payroll.
    """
    if type(start) is not date or type(end_inclusive) is not date:
        msg = "Start and end must be dates"
        raise ValueError(msg)
    if end_inclusive < start:
        msg = "End date precedes start date"
        raise ValueError(msg)
    if not fte.is_finite() or fte < 0:
        msg = "FTE must be a finite nonnegative Decimal"
        raise ValueError(msg)
    validated = tuple(MonthlySalaryRate.model_validate(r.model_dump()) for r in rates)
    if len({r.rate_id for r in validated}) != len(validated):
        msg = "Duplicate monthly rate identity"
        raise ValueError(msg)
    ordered = sorted(validated, key=lambda r: r.effective_from)
    if any(a.effective_to > b.effective_from for a, b in pairwise(ordered)):
        msg = "Monthly salary rates overlap"
        raise ValueError(msg)
    month = date(start.year, start.month, 1)
    rows: list[MonthlyBudgetRow] = []
    while month <= end_inclusive:
        days = monthrange(month.year, month.month)[1]
        first = max(start, month)
        last = min(end_inclusive, date(month.year, month.month, days))
        rows.extend(_month_rows(month, first, last, fte, ordered))
        if month.year == date.max.year and month.month == date.max.month:
            break
        month = _next_month(month)
    return MonthlyBudget(
        "calendar_month_salary_scenario_v1",
        start,
        end_inclusive,
        fte,
        tuple(rows),
        sum((r.amount for r in rows), Fraction(0)),
    )
