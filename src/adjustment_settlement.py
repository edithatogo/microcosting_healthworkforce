# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Reconcile reviewed entitlement against matched payroll credits."""

from dataclasses import dataclass
from fractions import Fraction
from typing import Self
lazy from datetime import date
lazy from decimal import Decimal

from pydantic import Field, model_validator

from src.unit_quotes import QuoteModel


class AdjustmentLine(QuoteModel):
    """One matched component and payroll interval in the settlement currency."""

    line_id: str
    component: str
    starts_on: date
    ends_on: date
    entitled: Decimal = Field(ge=0, allow_inf_nan=False)
    credited: Decimal = Field(ge=0, allow_inf_nan=False)
    entitlement_evidence: str
    credit_evidence: str

    @model_validator(mode="after")
    def nonempty_interval(self) -> Self:
        """Use a half-open interval for the matched payroll amounts."""
        if self.starts_on >= self.ends_on:
            msg = "Adjustment interval must be nonempty"
            raise ValueError(msg)
        return self


class AdjustmentSettlement(QuoteModel):
    """Explicitly reviewed eligibility, credit treatment and timing for one case."""

    case_id: str
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    crystallised_on: date
    reviewed_on: date
    as_known_on: date
    planned_payment_on: date | None
    review_evidence: str
    lines: tuple[AdjustmentLine, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def reviewed_ledger(self) -> Self:
        """Reject duplicated or overlapping credits and unavailable evidence."""
        if not self.crystallised_on <= self.reviewed_on <= self.as_known_on:
            msg = "Review must follow crystallisation and meet the knowledge cutoff"
            raise ValueError(msg)
        if (
            self.planned_payment_on is not None
            and self.planned_payment_on < self.crystallised_on
        ):
            msg = "Planned payment cannot precede crystallisation"
            raise ValueError(msg)
        if len({line.line_id.strip() for line in self.lines}) != len(self.lines):
            msg = "Duplicate adjustment line identity"
            raise ValueError(msg)
        latest: dict[str, date] = {}
        for line in sorted(self.lines, key=lambda item: item.starts_on):
            component = line.component.strip()
            if component in latest and line.starts_on < latest[component]:
                msg = "Overlapping adjustment intervals for a component"
                raise ValueError(msg)
            latest[component] = line.ends_on
        return self


@dataclass(frozen=True)
class AdjustmentBalance:
    """Exact signed difference for each line and its full reviewed request."""

    request: AdjustmentSettlement
    differences: tuple[Fraction, ...]
    net_difference: Fraction


def reconcile_adjustment(request: AdjustmentSettlement) -> AdjustmentBalance:
    """Compare reviewed amounts without inferring cash paid or recoverability."""
    request = AdjustmentSettlement.model_validate(request.model_dump())
    differences = tuple(
        Fraction(line.entitled) - Fraction(line.credited) for line in request.lines
    )
    return AdjustmentBalance(request, differences, sum(differences, Fraction(0)))
