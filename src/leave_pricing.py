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

    def select(self, base_pay: Fraction) -> LeaveLoadingAlternative:
        """Keep supplied election days as an explicitly allocated quantity."""
        return select_leave_loading_alternative(
            base_pay,
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
    for index, row in enumerate(rows):
        supplied = row.choice.loading_comparison
        if supplied is None:
            continue
        if has_cap or any(
            item.quote.component == "leave_loading"
            for item in row.pricing.pricing.rows[1:]
        ):
            msg = "Loading comparison cannot combine with a loading quote or cap"
            raise ValueError(msg)
        comparison = LeaveLoadingComparison.model_validate(dict(supplied))
        if comparison.comparison_id is None:
            alternative = comparison.select(row.pricing.pricing.rows[0].cost)
            rows[index] = replace(row, loading_alternative=alternative)
        else:
            groups.setdefault(comparison.comparison_id, []).append((index, comparison))
    for group in groups.values():
        _allocate_grouped_loading(rows, group)


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
        rows[index].pricing.pricing.rows[0].cost * Fraction(rate) for index, _ in group
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
