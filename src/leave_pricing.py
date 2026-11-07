# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Price explicit leave exposures without inferring payroll or continuation rules."""

from dataclasses import dataclass
from fractions import Fraction
from typing import Literal
lazy from datetime import date

from src.historical_hours import select_normal_hours
from src.normal_pay import HoursPricingRequest, price_selected_hours
from src.paid_leave import build_paid_leave
from src.unit_quotes import QuoteModel, UnitQuoteRelease
lazy from src.historical_hours import NormalHoursSelection
lazy from src.normal_pay import SelectedHoursPricing
lazy from src.paid_leave import LeaveExposureRow, PaidLeaveSchedule
lazy from src.unit_quotes import QuoteQuantity


def allocate_leave_loading_hours(
    eligible_hours: tuple[Fraction, ...],
    cap_hours: Fraction,
    prior_loaded_hours: Fraction,
) -> tuple[Fraction, ...]:
    """Allocate an explicit loading cap to eligible portions in payroll order.

    Supply the reviewed cap and prior consumption in the same hours unit.
    The returned hours can price loading separately from base leave pay.
    """
    if (
        cap_hours < 0
        or not 0 <= prior_loaded_hours <= cap_hours
        or any(hours < 0 for hours in eligible_hours)
    ):
        msg = "Leave loading hours and prior cap consumption must be valid"
        raise ValueError(msg)
    remaining = cap_hours - prior_loaded_hours
    allocated: list[Fraction] = []
    for hours in eligible_hours:
        loaded = min(hours, remaining)
        allocated.append(loaded)
        remaining -= loaded
    return tuple(allocated)


class LeavePriceSelection(QuoteModel):
    """An explicit price/exposure choice for exactly one schedule interval."""

    starts_on: date
    ends_on: date
    valuation_method: Literal["dated_row_start", "explicit_snapshot"]
    valuation_basis: str
    pricing: HoursPricingRequest
    allowances: tuple[QuoteQuantity, ...]


@dataclass(frozen=True)
class PricedLeaveRow:
    """Independent leave-state axes and the selected exact component prices."""

    exposure: LeaveExposureRow
    choice: LeavePriceSelection
    pricing: SelectedHoursPricing


@dataclass(frozen=True)
class PricedLeave:
    """Rebuilt source/scenario evidence and unrounded exposure cost, not cash due."""

    method_id: str
    schedule: PaidLeaveSchedule
    selection: NormalHoursSelection
    currency: str
    rows: tuple[PricedLeaveRow, ...]
    total: Fraction


def _choices(
    schedule: PaidLeaveSchedule,
    choices: tuple[LeavePriceSelection, ...],
) -> dict[tuple[date, date], LeavePriceSelection]:
    choices = tuple(LeavePriceSelection.model_validate(dict(c)) for c in choices)
    by_interval = {(c.starts_on, c.ends_on): c for c in choices}
    expected = {(r.starts_on, r.ends_on) for r in schedule.rows}
    if len(by_interval) != len(choices) or by_interval.keys() != expected:
        msg = "Exactly one price selection is required for every schedule interval"
        raise ValueError(msg)
    ids = [
        identity
        for c in choices
        for identity in (c.pricing.quantity_id, *(q.quantity_id for q in c.allowances))
    ]
    if len(set(ids)) != len(ids):
        msg = "Duplicate quantity identity across leave price selections"
        raise ValueError(msg)
    return by_interval


def _dated_coverage(
    release: UnitQuoteRelease,
    choice: LeavePriceSelection,
) -> None:
    if choice.valuation_method == "explicit_snapshot":
        return
    if choice.pricing.valued_on != choice.starts_on:
        msg = "Dated leave pricing requires the interval start valuation date"
        raise ValueError(msg)
    by_id = {q.quote_id: q for q in release.quotes}
    for identity in (choice.pricing.quote_id, *(q.quote_id for q in choice.allowances)):
        quote = by_id.get(identity)
        if quote is None or not (
            quote.starts_on <= choice.starts_on and choice.ends_on <= quote.ends_on
        ):
            msg = "Selected dated quotes must cover the whole leave interval"
            raise ValueError(msg)


def price_paid_leave(
    release: UnitQuoteRelease,
    selection: NormalHoursSelection,
    schedule: PaidLeaveSchedule,
    choices: tuple[LeavePriceSelection, ...],
) -> PricedLeave:
    """Compose reviewed inputs and separately declared salary/allowance exposure.

    Rebuild leave and hours from original declarations, not supplied derived totals.
    Each schedule row must have one choice with its exact pay-equivalent weeks.
    Dated choices require prices covering the whole interval; callers explicitly
    split the leave request at price boundaries. Snapshot choices can deliberately
    hold a price fixed and retain their counterfactual basis. Allowance quantities
    are supplied independently, never automatically scaled by pay factor or hours.
    Unknown accrual/debit state remains unknown. Advance instructions are retained
    without creating another price quantity or claiming an actual cash payment.
    """
    release = UnitQuoteRelease.model_validate(release.model_dump())
    schedule = build_paid_leave(schedule.policy, schedule.request)
    selection = select_normal_hours(selection.rule, selection.request, selection.rows)
    policy = schedule.policy
    if (policy.jurisdiction, policy.employer, policy.classification) != (
        release.jurisdiction,
        release.employer,
        release.classification,
    ) or policy.as_known_on != release.as_known_on:
        msg = "Leave policy and price release require the same scope and knowledge date"
        raise ValueError(msg)
    if selection.request.leave_starts_on != schedule.request.starts_on:
        msg = "Selected hours must use the same leave commencement date"
        raise ValueError(msg)
    selected = _choices(schedule, choices)
    rows: list[PricedLeaveRow] = []
    for exposure in schedule.rows:
        choice = selected[exposure.starts_on, exposure.ends_on]
        request = HoursPricingRequest.model_validate(dict(choice.pricing))
        if Fraction(request.week_quantity) != exposure.salary_equivalent_weeks:
            msg = "Price exposure must equal the schedule pay-equivalent weeks"
            raise ValueError(msg)
        _dated_coverage(release, choice)
        priced = price_selected_hours(release, selection, request, choice.allowances)
        rows.append(PricedLeaveRow(exposure, choice, priced))
    return PricedLeave(
        "paid_leave_selected_hours_pricing_v1",
        schedule,
        selection,
        release.currency,
        tuple(rows),
        sum((r.pricing.pricing.total for r in rows), Fraction(0)),
    )
