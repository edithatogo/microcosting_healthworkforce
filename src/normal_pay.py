# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Price selected hours and supplied allowances without implicit payroll rules."""

from dataclasses import dataclass
from fractions import Fraction
from typing import Self
lazy from datetime import date

from pydantic import model_validator

from src.historical_hours import select_normal_hours
from src.unit_quotes import QuoteModel, QuoteQuantity, UnitQuoteRelease, price_units
lazy from src.historical_hours import NormalHoursSelection
lazy from src.unit_quotes import NonnegativeQuantity, UnitQuoteResult


class HoursPricingRequest(QuoteModel):
    """Explicit weekly exposure, snapshot and base-inclusion declarations."""

    quantity_id: str
    quote_id: str
    week_quantity: NonnegativeQuantity
    valued_on: date
    basis: str
    base_included_components: tuple[str, ...]
    base_inclusion_basis: str
    exclusive_component_groups: tuple[tuple[str, ...], ...]
    allowance_interaction_basis: str

    @model_validator(mode="after")
    def distinct_inclusions(self) -> Self:
        """Require distinct meaningful component names, including an empty set."""
        values = self.base_included_components
        if len(set(values)) != len(values) or any(not v.strip() for v in values):
            msg = "Base included components must be distinct nonblank names"
            raise ValueError(msg)
        groups = self.exclusive_component_groups
        if any(
            len(group) <= 1
            or len(set(group)) != len(group)
            or any(not name.strip() for name in group)
            for group in groups
        ) or len({frozenset(group) for group in groups}) != len(groups):
            msg = "Exclusive component groups require distinct nonblank alternatives"
            raise ValueError(msg)
        return self


@dataclass(frozen=True)
class SelectedHoursPricing:
    """Recomputed quantity selection plus exact source-priced component ledger."""

    method_id: str
    selection: NormalHoursSelection
    request: HoursPricingRequest
    pricing: UnitQuoteResult


def price_selected_hours(
    release: UnitQuoteRelease,
    selection: NormalHoursSelection,
    request: HoursPricingRequest,
    allowances: tuple[QuoteQuantity, ...],
) -> SelectedHoursPricing:
    """Price a selected weekly hours base over an explicit number of weeks.

    The base quote must use the exact unit 'hour'. Allowance quantities retain
    their own independently supplied units and amounts; they are not multiplied
    by the selected salary hours. All quantities share this valuation snapshot,
    while repeated calls can use explicitly selected dated prices/exposures.
    Different components are additive only as declared. Base inclusions and
    duplicate allowance components are rejected to prevent duplicate charges.
    Continuation eligibility, allowance proration, accrual, actual work, payroll
    dates and cover remain separate. This computes a price exposure, not pay due.
    """
    release = UnitQuoteRelease.model_validate(release.model_dump())
    request = HoursPricingRequest.model_validate(dict(request))
    selection = select_normal_hours(selection.rule, selection.request, selection.rows)
    allowances = tuple(QuoteQuantity.model_validate(dict(q)) for q in allowances)
    rule = selection.rule
    if (release.jurisdiction, release.employer, release.classification) != (
        rule.jurisdiction,
        rule.employer,
        rule.classification,
    ):
        msg = "Hours selection and price release must have the same source scope"
        raise ValueError(msg)
    if release.as_known_on != rule.as_known_on:
        msg = "Hours selection and prices require the same knowledge date"
        raise ValueError(msg)
    by_id = {quote.quote_id: quote for quote in release.quotes}
    base = by_id.get(request.quote_id)
    if base is None:
        msg = "No quote for the selected hours base"
        raise ValueError(msg)
    included = {base.component, *request.base_included_components}
    seen: set[str] = set()
    for quantity in allowances:
        if quantity.valued_on != request.valued_on:
            msg = "Allowance quantities must share the valuation snapshot"
            raise ValueError(msg)
        quote = by_id.get(quantity.quote_id)
        if quote is None:
            msg = "No quote for the supplied allowance"
            raise ValueError(msg)
        if quote.component in included:
            msg = "Allowance component is already included in the priced base"
            raise ValueError(msg)
        if quote.component in seen:
            msg = "Duplicate component across supplied allowances"
            raise ValueError(msg)
        seen.add(quote.component)
    active_components = included | seen
    if any(
        len(active_components.intersection(group)) > 1
        for group in request.exclusive_component_groups
    ):
        msg = "Mutually exclusive components cannot share this priced exposure"
        raise ValueError(msg)
    base_quantity = QuoteQuantity(
        quantity_id=request.quantity_id,
        quote_id=request.quote_id,
        unit="hour",
        quantity=selection.selected_hours_per_week * Fraction(request.week_quantity),
        valued_on=request.valued_on,
        quantity_kind="analyst_assumption",
        basis=request.basis,
    )
    result = price_units(release, (base_quantity, *allowances))
    return SelectedHoursPricing(
        "selected_hours_with_explicit_allowances_v1",
        selection,
        request,
        result,
    )
