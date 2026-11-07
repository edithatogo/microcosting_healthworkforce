# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Price explicit leave exposures without inferring payroll or continuation rules."""

from dataclasses import dataclass, replace
from fractions import Fraction
from itertools import pairwise
from typing import Literal
lazy from datetime import date

from src.historical_hours import select_normal_hours
from src.normal_pay import HoursPricingRequest, price_selected_hours
from src.paid_leave import build_paid_leave
from src.unit_quotes import (
    NonnegativeQuantity,
    QuoteModel,
    QuoteQuantity,
    UnitQuoteRelease,
    price_units,
)
lazy from src.historical_hours import NormalHoursSelection
lazy from src.normal_pay import SelectedHoursPricing
lazy from src.paid_leave import LeaveExposureRow, PaidLeaveSchedule
lazy from src.unit_quotes import UnitQuoteResult


@dataclass(frozen=True)
class LeaveLoadingAlternative:
    """Separate the selected cash loading from any elected leave days."""

    cash: Fraction
    additional_days: Fraction


def select_leave_loading_alternative(
    base_leave_pay: Fraction,
    loading_rate: Fraction,
    forgone_penalties: Fraction | None,
    *,
    elected_days: Fraction | None = None,
) -> LeaveLoadingAlternative:
    """Compare reviewed amounts for the same leave exposure and currency.

    A supplied election must already be verified for the relevant entitlement
    period. Its days remain a quantity for downstream leave accounting.
    """
    if (
        base_leave_pay < 0
        or loading_rate < 0
        or (forgone_penalties is not None and forgone_penalties < 0)
        or (elected_days is not None and elected_days <= 0)
    ):
        msg = "Leave loading amounts must be nonnegative and elected days positive"
        raise ValueError(msg)
    if elected_days is not None:
        return LeaveLoadingAlternative(Fraction(0), elected_days)
    if forgone_penalties is None:
        msg = "Cash leave loading requires reviewed forgone penalties"
        raise ValueError(msg)
    return LeaveLoadingAlternative(
        max(base_leave_pay * loading_rate, forgone_penalties),
        Fraction(0),
    )


@dataclass(frozen=True)
class CombinedLeaveHours:
    """Total capped hours and the feasible range of loading-eligible hours."""

    total: Fraction
    minimum_loaded: Fraction
    maximum_loaded: Fraction


def qualifying_shift_leave_credit(
    worked_shifts: int,
    required_shifts: int,
    full_time_credit: Fraction,
    ordinary_hours_fraction: Fraction,
) -> Fraction:
    """Calculate one reviewed period's credit before applying the annual cap."""
    if worked_shifts < 0 or required_shifts <= 0:
        msg = "Qualifying shift counts require a positive threshold"
        raise ValueError(msg)
    if full_time_credit < 0 or not 0 < ordinary_hours_fraction <= 1:
        msg = "Leave credit and ordinary hours fraction must be valid"
        raise ValueError(msg)
    if worked_shifts < required_shifts:
        return Fraction(0)
    return full_time_credit * ordinary_hours_fraction


def nsw_general_shift_leave_credit(
    worked_shifts: int,
    ordinary_weekly_hours: Fraction,
    *,
    rounding_increment_hours: Fraction | None = None,
) -> Fraction:
    """Apply historical NSW Conditions Award 16(i)(b) to reviewed shifts.

    The caller establishes coverage, shift eligibility and the rounding increment
    for a worker below 38 weekly hours. The count covers one qualifying year.
    """
    if worked_shifts < 0 or ordinary_weekly_hours <= 0:
        msg = "Shift count and ordinary weekly hours must be valid"
        raise ValueError(msg)
    if worked_shifts == 0:
        return Fraction(0)
    annual_shift_threshold = 35
    full_time_weekly_hours = 38
    if worked_shifts >= annual_shift_threshold:
        return ordinary_weekly_hours
    if ordinary_weekly_hours >= full_time_weekly_hours:
        return Fraction(full_time_weekly_hours * worked_shifts, annual_shift_threshold)
    if rounding_increment_hours is None or rounding_increment_hours <= 0:
        msg = "Below 38 weekly hours, supply a reviewed rounding increment"
        raise ValueError(msg)
    exact_hours = ordinary_weekly_hours * Fraction(
        worked_shifts,
        annual_shift_threshold,
    )
    rounded_units = (exact_hours / rounding_increment_hours + Fraction(1, 2)) // 1
    return rounded_units * rounding_increment_hours


@dataclass(frozen=True)
class WeekendLeaveShift:
    """Reviewed ordinary shift duration and hours attributable to the weekend."""

    shift_hours: Fraction
    weekend_hours: Fraction


def victorian_medical_scientist_weekend_leave_credit(
    weekends: tuple[tuple[WeekendLeaveShift, ...], ...],
    *,
    part_time: bool,
    nes_credit_hours: Fraction,
) -> Fraction:
    """Calculate weekend leave hours for one reviewed 12-month roster window.

    The same arithmetic applies under clauses 60.7 (2017-2021) and
    61.8 (2021-2025). The caller establishes the operative agreement.

    Group ordinary shifts by weekend. Supply reviewed weekend attribution for
    shifts crossing a day boundary and zero NES credit when inapplicable.
    """
    if nes_credit_hours < 0 or any(
        not 0 <= shift.weekend_hours <= shift.shift_hours
        for weekend in weekends
        for shift in weekend
    ):
        msg = "Weekend hours must fit the shift and NES credit must be nonnegative"
        raise ValueError(msg)
    minimum_shift_hours = 4
    qualifying_hours = Fraction(0)
    for weekend in weekends:
        eligible = tuple(
            shift
            for shift in weekend
            if shift.shift_hours > minimum_shift_hours and shift.weekend_hours > 0
        )
        if part_time and eligible:
            longest_hours = max(shift.shift_hours for shift in eligible)
            creditable_hours = {
                shift.weekend_hours
                for shift in eligible
                if shift.shift_hours == longest_hours
            }
            if len(creditable_hours) > 1:
                msg = "Equal-length shifts require a reviewed weekend credit selection"
                raise ValueError(msg)
            qualifying_hours += next(iter(creditable_hours))
        else:
            qualifying_hours += sum(
                (shift.weekend_hours for shift in eligible),
                Fraction(0),
            )
    agreement_credit = min(Fraction(38), qualifying_hours / 2)
    return max(agreement_credit, nes_credit_hours)


def combined_leave_hours(
    loading_eligible: Fraction,
    base_only: Fraction,
    cap: Fraction,
) -> CombinedLeaveHours:
    """Bound the loading basis when a shared cap has no reviewed priority."""
    if min(loading_eligible, base_only, cap) < 0:
        msg = "Combined leave hours and cap must be nonnegative"
        raise ValueError(msg)
    total = min(loading_eligible + base_only, cap)
    return CombinedLeaveHours(
        total,
        max(Fraction(0), total - base_only),
        min(loading_eligible, total),
    )


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
    return _allocate_cap(eligible_hours, cap_hours - prior_loaded_hours)


def _allocate_cap(
    amounts: tuple[Fraction, ...],
    remaining: Fraction,
) -> tuple[Fraction, ...]:
    allocated: list[Fraction] = []
    for amount in amounts:
        used = min(amount, remaining)
        allocated.append(used)
        remaining -= used
    return tuple(allocated)


def price_leave_loading(
    loaded_hours: tuple[Fraction, ...],
    hourly_loading: tuple[Fraction, ...],
    monetary_cap: Fraction,
    prior_paid: Fraction,
) -> tuple[Fraction, ...]:
    """Apply reviewed hourly loading prices and a separate monetary maximum.

    Inputs share one currency and cap period. Hours are already allocated
    to eligible portions and ordered for payment. The caller supplies the
    prorated maximum and prior payments for that period.
    """
    if (
        monetary_cap < 0
        or not 0 <= prior_paid <= monetary_cap
        or any(hours < 0 for hours in loaded_hours)
        or any(price < 0 for price in hourly_loading)
    ):
        msg = "Leave loading prices, hours and prior payments must be valid"
        raise ValueError(msg)
    amounts = tuple(
        hours * price for hours, price in zip(loaded_hours, hourly_loading, strict=True)
    )
    return _allocate_cap(amounts, monetary_cap - prior_paid)


class LeaveLoadingComparison(QuoteModel):
    """Reviewed loading inputs for one priced interval in release currency."""

    rate: NonnegativeQuantity
    forgone_penalties: NonnegativeQuantity | None = None
    elected_days: NonnegativeQuantity | None = None
    evidence: str
    comparison_id: str | None = None
    loading_basis_pay: NonnegativeQuantity | None = None

    def standard_basis(self, base_pay: Fraction) -> Fraction:
        """Use a reviewed ordinary-rate basis when it differs from ledger pay."""
        return (
            base_pay
            if self.loading_basis_pay is None
            else Fraction(self.loading_basis_pay)
        )

    def select(self, base_pay: Fraction) -> LeaveLoadingAlternative:
        """Keep supplied election days as an explicitly allocated quantity."""
        return select_leave_loading_alternative(
            self.standard_basis(base_pay),
            Fraction(self.rate),
            None
            if self.forgone_penalties is None
            else Fraction(self.forgone_penalties),
            elected_days=None
            if self.elected_days is None
            else Fraction(self.elected_days),
        )


class AdvanceLoadingTiming(QuoteModel):
    """Reviewed facts for loading deferred until leave entitlement is reached."""

    leave_taken_on: date
    entitled_on: date
    employment_confirmed_through: date
    as_known_on: date
    ordinary_penalties_already_paid: bool
    evidence: str

    def payable_on(self) -> date | None:
        """Return the entitlement date only once continued employment is known."""
        facts = AdvanceLoadingTiming.model_validate(dict(self))
        if (
            facts.leave_taken_on >= facts.entitled_on
            or facts.employment_confirmed_through > facts.as_known_on
        ):
            msg = "Advance loading requires valid leave and employment evidence dates"
            raise ValueError(msg)
        if (
            facts.ordinary_penalties_already_paid
            or facts.employment_confirmed_through < facts.entitled_on
        ):
            return None
        return facts.entitled_on


class SeparationLoadingEligibility(QuoteModel):
    """Reviewed separation facts for the historical NSW loading provision."""

    separated_on: date
    as_known_on: date
    reason: Literal[
        "retirement",
        "resignation",
        "employer_termination",
        "misconduct",
        "other",
    ]
    entitled_loading_weeks: NonnegativeQuantity
    evidence: str

    def eligible_weeks(self) -> Fraction:
        """Return the exposure admitted under clause 17B(g) and (h)."""
        facts = SeparationLoadingEligibility.model_validate(dict(self))
        if facts.separated_on > facts.as_known_on:
            msg = "Separation must be known at the valuation cutoff"
            raise ValueError(msg)
        if facts.reason == "other":
            msg = "Separation reason is outside the reviewed loading provision"
            raise ValueError(msg)
        if facts.reason in {"resignation", "misconduct"}:
            return Fraction(0)
        return Fraction(facts.entitled_loading_weeks)


class AdvanceLeaveTermination(QuoteModel):
    """Reviewed ordinary-pay amounts for a single advance-leave settlement."""

    terminated_on: date
    service_year_completed_on: date
    as_known_on: date
    advance_ordinary_pay: NonnegativeQuantity
    ordinary_pay_due: NonnegativeQuantity
    evidence: str

    def excess_ordinary_pay(self) -> Fraction:
        """Return the clause 17A(i) excess before any payroll deduction."""
        facts = AdvanceLeaveTermination.model_validate(dict(self))
        if facts.terminated_on > facts.as_known_on:
            msg = "Termination must be known at the valuation cutoff"
            raise ValueError(msg)
        if facts.terminated_on >= facts.service_year_completed_on:
            return Fraction(0)
        return max(
            Fraction(0),
            Fraction(facts.advance_ordinary_pay) - Fraction(facts.ordinary_pay_due),
        )


class AdvanceLoadingPrices(QuoteModel):
    """Explicit weekly salary and benchmark selections for deferred loading."""

    salary_quote_id: str
    benchmark_quote_id: str
    eligible_weeks: NonnegativeQuantity
    loading_rate: NonnegativeQuantity


@dataclass(frozen=True)
class DeferredLeaveLoading:
    """Exact loading amount and the dated prices behind it."""

    timing: AdvanceLoadingTiming
    prices: AdvanceLoadingPrices
    ledger: UnitQuoteResult
    amount: Fraction


def price_advance_loading(
    release: UnitQuoteRelease,
    timing: AdvanceLoadingTiming,
    prices: AdvanceLoadingPrices,
) -> DeferredLeaveLoading | None:
    """Use the entitlement date for both reviewed weekly price selections."""
    payable_on = timing.payable_on()
    if release.as_known_on != timing.as_known_on:
        msg = "Advance loading and the price release must share a knowledge date"
        raise ValueError(msg)
    if payable_on is None:
        return None
    prices = AdvanceLoadingPrices.model_validate(dict(prices))
    ledger, amount = _price_capped_weekly_loading(
        release,
        prices,
        prices.eligible_weeks,
        payable_on,
        timing.evidence,
    )
    return DeferredLeaveLoading(timing, prices, ledger, amount)


def _price_capped_weekly_loading(
    release: UnitQuoteRelease,
    prices: AdvanceLoadingPrices,
    weeks: NonnegativeQuantity,
    valued_on: date,
    evidence: str,
) -> tuple[UnitQuoteResult, Fraction]:
    ledger = price_units(
        release,
        tuple(
            QuoteQuantity(
                quantity_id=label,
                quote_id=quote_id,
                unit="week",
                quantity=weeks,
                valued_on=valued_on,
                quantity_kind="analyst_assumption",
                basis=evidence,
            )
            for label, quote_id in (
                ("salary", prices.salary_quote_id),
                ("benchmark", prices.benchmark_quote_id),
            )
        ),
    )
    salary, benchmark = ledger.rows
    if (salary.quote.component, benchmark.quote.component) != ("salary", "benchmark"):
        msg = "Capped loading requires a salary quote and a benchmark quote"
        raise ValueError(msg)
    amount = min(salary.cost, benchmark.cost) * Fraction(prices.loading_rate)
    return ledger, amount


def price_separation_loading(
    release: UnitQuoteRelease,
    eligibility: SeparationLoadingEligibility,
    prices: AdvanceLoadingPrices,
    *,
    valued_on: date,
    valuation_evidence: str,
) -> tuple[UnitQuoteResult, Fraction] | None:
    """Price eligible separation loading on an explicitly reviewed rate date."""
    weeks = eligibility.eligible_weeks()
    if release.as_known_on != eligibility.as_known_on:
        msg = "Separation and the price release must share a knowledge date"
        raise ValueError(msg)
    if not valuation_evidence.strip() or valued_on > eligibility.as_known_on:
        msg = "Separation loading requires reviewed valuation evidence at cutoff"
        raise ValueError(msg)
    if not weeks:
        return None
    prices = AdvanceLoadingPrices.model_validate(dict(prices))
    if Fraction(prices.eligible_weeks) != weeks:
        msg = "Selected pricing weeks must equal eligible separation weeks"
        raise ValueError(msg)
    return _price_capped_weekly_loading(
        release,
        prices,
        weeks,
        valued_on,
        valuation_evidence,
    )


class VictorianLeaveLoadingComparison(QuoteModel):
    """Reviewed clause 60.8 inputs for one complete comparison interval."""

    premium_inclusive_pay: NonnegativeQuantity
    remaining_loading_cap: NonnegativeQuantity
    evidence: str
    comparison_id: str | None = None


class LeavePriceSelection(QuoteModel):
    """An explicit price/exposure choice for exactly one schedule interval."""

    starts_on: date
    ends_on: date
    valuation_method: Literal["dated_row_start", "explicit_snapshot"]
    valuation_basis: str
    pricing: HoursPricingRequest
    allowances: tuple[QuoteQuantity, ...]
    loading_accrued_on: date | None = None
    loading_comparison: LeaveLoadingComparison | None = None
    victorian_loading: VictorianLeaveLoadingComparison | None = None


class LeaveLoadingMoneyCap(QuoteModel):
    """Reviewed monetary maximum and prior paid amount in release currency."""

    starts_on: date
    ends_on: date
    maximum: NonnegativeQuantity
    prior_paid: NonnegativeQuantity
    evidence: str


@dataclass(frozen=True)
class PricedLeaveRow:
    """Independent leave-state axes and the selected exact component prices."""

    exposure: LeaveExposureRow
    choice: LeavePriceSelection
    pricing: SelectedHoursPricing
    loading_reduction: Fraction = Fraction(0)
    loading_alternative: LeaveLoadingAlternative | None = None

    @property
    def total(self) -> Fraction:
        """Combine the base ledger and exactly one loading path."""
        cash = (
            self.loading_alternative.cash if self.loading_alternative else Fraction(0)
        )
        return self.pricing.pricing.total - self.loading_reduction + cash


@dataclass(frozen=True)
class PricedLeave:
    """Rebuilt source/scenario evidence and unrounded exposure cost, not cash due."""

    method_id: str
    schedule: PaidLeaveSchedule
    selection: NormalHoursSelection
    currency: str
    rows: tuple[PricedLeaveRow, ...]
    total: Fraction
    loading_cap: LeaveLoadingMoneyCap | None = None
    loading_caps: tuple[LeaveLoadingMoneyCap, ...] = ()


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


def _apply_loading_comparisons(
    rows: list[PricedLeaveRow],
    *,
    has_cap: bool,
) -> None:
    """Compare each declared cash interval once and allocate its winning basis."""
    groups: dict[str, list[tuple[int, LeaveLoadingComparison]]] = {}
    victorian_groups: dict[str, list[tuple[int, VictorianLeaveLoadingComparison]]] = {}
    for index, row in enumerate(rows):
        supplied = row.choice.loading_comparison
        victorian = row.choice.victorian_loading
        if (supplied or victorian) and (
            has_cap
            or any(
                item.quote.component == "leave_loading"
                for item in row.pricing.pricing.rows[1:]
            )
        ):
            msg = "Loading comparison cannot combine with a loading quote or cap"
            raise ValueError(msg)
        base_pay = row.pricing.pricing.rows[0].cost
        if victorian is not None:
            if supplied is not None:
                msg = "Select only one loading comparison"
                raise ValueError(msg)
            reviewed = VictorianLeaveLoadingComparison.model_validate(dict(victorian))
            if reviewed.comparison_id is None:
                _allocate_victorian_loading(rows, [(index, reviewed)])
            else:
                victorian_groups.setdefault(reviewed.comparison_id, []).append(
                    (index, reviewed),
                )
        elif supplied is not None:
            comparison = LeaveLoadingComparison.model_validate(dict(supplied))
            if comparison.comparison_id is None:
                alternative = comparison.select(base_pay)
                rows[index] = replace(row, loading_alternative=alternative)
            else:
                groups.setdefault(comparison.comparison_id, []).append(
                    (index, comparison),
                )
    for group in groups.values():
        _allocate_grouped_loading(rows, group)

    for group in victorian_groups.values():
        _allocate_victorian_loading(rows, group)


def _allocate_victorian_loading(
    rows: list[PricedLeaveRow],
    group: list[tuple[int, VictorianLeaveLoadingComparison]],
) -> None:
    reviewed = group[0][1]
    if any(item != reviewed for _, item in group) or any(
        rows[left].exposure.ends_on != rows[right].exposure.starts_on
        for (left, _), (right, _) in pairwise(group)
    ):
        msg = "Victorian loading requires contiguous rows with identical period inputs"
        raise ValueError(msg)
    bases = [rows[index].pricing.pricing.rows[0].cost for index, _ in group]
    total_base = sum(bases, Fraction(0))
    cash = victorian_medical_scientist_leave_loading(
        total_base,
        Fraction(reviewed.premium_inclusive_pay),
        Fraction(reviewed.remaining_loading_cap),
    )
    # Allocate for reporting by ordinary pay, or evenly when ordinary pay is zero.
    for (index, _), base in zip(group, bases, strict=True):
        share = base / total_base if total_base else Fraction(1, len(group))
        rows[index] = replace(
            rows[index],
            loading_alternative=LeaveLoadingAlternative(cash * share, Fraction(0)),
        )


def _allocate_grouped_loading(
    rows: list[PricedLeaveRow],
    group: list[tuple[int, LeaveLoadingComparison]],
) -> None:
    rate = group[0][1].rate
    if any(
        comparison.rate != rate
        or comparison.elected_days is not None
        or comparison.forgone_penalties is None
        for _, comparison in group
    ) or any(
        rows[left].exposure.ends_on != rows[right].exposure.starts_on
        for (left, _), (right, _) in pairwise(group)
    ):
        msg = "Grouped loading requires contiguous cash rows, penalties and one rate"
        raise ValueError(msg)
    floors = [
        comparison.standard_basis(rows[index].pricing.pricing.rows[0].cost)
        * Fraction(rate)
        for index, comparison in group
    ]
    penalties = [Fraction(comparison.forgone_penalties or 0) for _, comparison in group]
    winning = floors if sum(floors) >= sum(penalties) else penalties
    for (index, _), cash in zip(group, winning, strict=True):
        rows[index] = replace(
            rows[index],
            loading_alternative=LeaveLoadingAlternative(cash, Fraction(0)),
        )


def _apply_loading_caps(
    rows: list[PricedLeaveRow],
    caps: tuple[LeaveLoadingMoneyCap, ...],
) -> None:
    """Allocate each period's remaining cap only to leave accrued in that period."""
    caps = tuple(
        sorted(
            (LeaveLoadingMoneyCap.model_validate(dict(cap)) for cap in caps),
            key=lambda cap: cap.starts_on,
        ),
    )
    if any(cap.starts_on >= cap.ends_on for cap in caps) or any(
        left.ends_on > right.starts_on for left, right in pairwise(caps)
    ):
        msg = "Loading cap periods must be nonempty and nonoverlapping"
        raise ValueError(msg)
    loading = [
        (index, item)
        for index, row in enumerate(rows)
        for item in row.pricing.pricing.rows[1:]
        if item.quote.component == "leave_loading"
    ]
    if not loading or any(item.quote.unit != "hour" for _, item in loading):
        msg = "Loading cap requires separately priced hourly leave loading"
        raise ValueError(msg)
    for index, _ in loading:
        accrued_on = rows[index].choice.loading_accrued_on
        if accrued_on is None or not any(
            cap.starts_on <= accrued_on < cap.ends_on for cap in caps
        ):
            msg = "Leave loading requires an accrual date within the cap period"
            raise ValueError(msg)
    for cap in caps:
        period_loading = [
            (index, item)
            for index, item in loading
            if (accrued_on := rows[index].choice.loading_accrued_on) is not None
            and cap.starts_on <= accrued_on < cap.ends_on
        ]
        capped = price_leave_loading(
            tuple(Fraction(item.quantity.quantity) for _, item in period_loading),
            tuple(Fraction(item.quote.amount) for _, item in period_loading),
            Fraction(cap.maximum),
            Fraction(cap.prior_paid),
        )
        for (index, item), cost in zip(period_loading, capped, strict=True):
            row = rows[index]
            rows[index] = replace(
                row,
                loading_reduction=row.loading_reduction + item.cost - cost,
            )


def price_paid_leave(
    release: UnitQuoteRelease,
    selection: NormalHoursSelection,
    schedule: PaidLeaveSchedule,
    choices: tuple[LeavePriceSelection, ...],
    *,
    loading_cap: LeaveLoadingMoneyCap | tuple[LeaveLoadingMoneyCap, ...] | None = None,
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
    _apply_loading_comparisons(rows, has_cap=bool(loading_cap))
    single_cap = loading_cap if isinstance(loading_cap, LeaveLoadingMoneyCap) else None
    multiple_caps = loading_cap if isinstance(loading_cap, tuple) else ()
    caps = (single_cap,) if single_cap is not None else multiple_caps
    if caps:
        _apply_loading_caps(rows, caps)
    return PricedLeave(
        "paid_leave_selected_hours_pricing_v1",
        schedule,
        selection,
        release.currency,
        tuple(rows),
        sum((row.total for row in rows), Fraction(0)),
        single_cap,
        multiple_caps,
    )


def victorian_medical_scientist_leave_loading(
    ordinary_pay: Fraction,
    premium_inclusive_pay: Fraction,
    remaining_loading_cap: Fraction,
) -> Fraction:
    """Value the additional cash under the Victorian 2017-2021 clause 60.8.

    Supply the reviewed cap balance and premium-inclusive pay for the same
    leave period and currency. The latter reflects average eligible earnings
    or the reviewed roster equivalent for weekend-only or permanent nights.
    """
    if min(ordinary_pay, premium_inclusive_pay, remaining_loading_cap) < 0:
        msg = "Victorian loading inputs must be nonnegative"
        raise ValueError(msg)
    standard_loading = min(ordinary_pay * Fraction(7, 40), remaining_loading_cap)
    return max(standard_loading, premium_inclusive_pay - ordinary_pay)


def victorian_hama_additional_leave_weeks(
    ordinary_hours_by_weekend: tuple[Fraction, ...],
    *,
    nes_shiftworker: bool,
) -> int:
    """Value additional leave for a completed service year under clause 74.4.

    Supply one reviewed ordinary-hours total per distinct weekend, and
    the applicable NES shiftworker decision for that same service year.
    """
    if any(hours < 0 for hours in ordinary_hours_by_weekend):
        msg = "Ordinary weekend hours must be nonnegative"
        raise ValueError(msg)
    qualifying_hours = 4
    qualifying_weekends = 10
    count = sum(hours > qualifying_hours for hours in ordinary_hours_by_weekend)
    return int(nes_shiftworker or count >= qualifying_weekends)


def victorian_hama_weekend_termination_pay(period_ordinary_pay: Fraction) -> Fraction:
    """Value clause 74.4(d) for a reviewed eligible partial-year termination.

    Supply ordinary pay since commencement or the last annual leave entitlement,
    as applicable to the reviewed period of less than one year.
    """
    if period_ordinary_pay < 0:
        msg = "Termination period ordinary pay must be nonnegative"
        raise ValueError(msg)
    return period_ordinary_pay / 48


def victorian_hama_leave_loading(
    ordinary_rate_wages: Fraction,
    *,
    over_agreement_pay: Fraction,
    shift_premiums: Fraction,
    weekend_premiums: Fraction,
    in_charge_allowances: Fraction,
) -> Fraction:
    """Value clause 74.7(a) for one reviewed, covered leave period.

    Supply ordinary-rate wages for normal hours and the four eligible
    supplements as separate amounts for the same period and currency.
    """
    supplements = (
        over_agreement_pay,
        shift_premiums,
        weekend_premiums,
        in_charge_allowances,
    )
    if any(amount < 0 for amount in supplements):
        msg = "HAMA leave supplements must be nonnegative"
        raise ValueError(msg)
    return select_leave_loading_alternative(
        ordinary_rate_wages,
        Fraction(7, 40),
        sum(supplements, Fraction(0)),
    ).cash
