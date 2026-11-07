# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Select source-qualified count bands without inferring eligibility or accrual."""

from dataclasses import dataclass
from datetime import date, timedelta
from fractions import Fraction
from itertools import pairwise
from typing import Literal, Self
from zoneinfo import ZoneInfo

from pydantic import Field, model_validator

from src.exclusive_quotes import (
    ExclusiveQuoteRule,
    QuoteExposureWindow,
    validate_quote_exposures,
)
from src.unit_quotes import (
    QuoteModel,
    QuoteQuantity,
    UnitQuote,
    UnitQuoteRelease,
    UnitQuoteResult,
    price_units,
)


class CountBand(QuoteModel):
    """Inclusive integer count interval; None explicitly means no entitlement."""

    band_id: str
    minimum: int = Field(ge=0)
    maximum: int = Field(ge=0)
    component: str | None

    @model_validator(mode="after")
    def valid_bounds(self) -> Self:
        """Do not accept reversed or implicitly unbounded bands."""
        if self.maximum < self.minimum:
            msg = "Count band bounds must be ordered"
            raise ValueError(msg)
        return self


class CountBandRule(QuoteModel):
    """Reviewed count thresholds and all required true eligibility predicates."""

    scope: ExclusiveQuoteRule
    bands: tuple[CountBand, ...] = Field(min_length=1)
    required_facts: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unambiguous(self) -> Self:
        """Every priced band names one declared component, without overlap."""
        components = [b.component for b in self.bands if b.component is not None]
        ordered = sorted(self.bands, key=lambda b: b.minimum)
        if (
            len({b.band_id for b in self.bands}) != len(self.bands)
            or len(set(components)) != len(components)
            or set(components) != set(self.scope.components)
            or any(a.maximum >= b.minimum for a, b in pairwise(ordered))
        ):
            msg = "Count bands require unique identities/components and no overlap"
            raise ValueError(msg)
        if len(set(self.required_facts)) != len(self.required_facts) or any(
            not name.strip() for name in self.required_facts
        ):
            msg = "Required facts must have unique nonblank identities"
            raise ValueError(msg)
        return self


class CountBandFact(QuoteModel):
    """One declared predicate with separate knowledge and effective coverage."""

    fact_id: str
    satisfied: bool
    effective_from: date
    effective_to: date
    basis: str
    input_kind: Literal["observed_case_evidence", "analyst_assumption"]
    known_on: date
    evidence_id: str
    evidence_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def nonempty_coverage(self) -> Self:
        """Keep effective fact coverage separate from its knowledge date."""
        if self.effective_to <= self.effective_from:
            msg = "Count fact requires nonempty effective coverage"
            raise ValueError(msg)
        return self


class CountBandCase(QuoteModel):
    """Complete constant-state exposure and its explicitly allocated quantity."""

    exposure: QuoteExposureWindow
    staff_count: int = Field(ge=0)
    count_and_facts_constant: bool
    facts: tuple[CountBandFact, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def constant_window(self) -> Self:
        """Require a separate allocation when a count or predicate changes."""
        if not self.count_and_facts_constant:
            msg = "Count and facts must be explicitly constant over the window"
            raise ValueError(msg)
        return self


@dataclass(frozen=True)
class CountBandSelection:
    """Retain suppressed price, original quantity and every negative predicate."""

    case: CountBandCase
    band: CountBand
    quote: UnitQuote | None
    disqualifying_facts: tuple[str, ...]
    amount: Fraction


@dataclass(frozen=True)
class CountBandResult:
    """Complete input lineage plus the exact shared quoted-unit price ledger."""

    method_id: Literal["count_band_quotes_v1"]
    rule: CountBandRule
    release: UnitQuoteRelease
    selections: tuple[CountBandSelection, ...]
    scenario: bool
    prices: UnitQuoteResult


def _rule(rule: CountBandRule) -> CountBandRule:
    raw = dict(rule)
    raw["scope"] = ExclusiveQuoteRule.model_validate(dict(rule.scope))
    raw["bands"] = tuple(CountBand.model_validate(dict(b)) for b in rule.bands)
    return CountBandRule.model_validate(raw)


def _case(case: CountBandCase) -> CountBandCase:
    raw = dict(case)
    raw["exposure"] = QuoteExposureWindow.model_validate(dict(case.exposure))
    raw["facts"] = tuple(CountBandFact.model_validate(dict(f)) for f in case.facts)
    return CountBandCase.model_validate(raw)


def price_count_bands(
    rule: CountBandRule,
    release: UnitQuoteRelease,
    cases: tuple[CountBandCase, ...],
) -> CountBandResult:
    """Price static or dated count/fact windows using explicit unit quantities.

    All predicates are required and AND-combined. A caller must resolve any
    source-specific OR/exception, count definition and service/selection test
    before declaring the corresponding fact. Counts/facts are constant per
    window; price changes also require an explicit split and quantity allocation.
    No highest rate, out-of-band extrapolation, duration proration or cash saving
    is inferred. This method is separate from a salary-inclusive hourly ledger.
    """
    rule = _rule(rule)
    release = UnitQuoteRelease.model_validate(release.model_dump())
    cases = tuple(_case(c) for c in cases)
    policy = rule.scope
    validate_quote_exposures(policy, release, tuple(c.exposure for c in cases))
    ordered = sorted(
        cases,
        key=lambda c: (
            c.exposure.resource_id,
            c.exposure.starts_at,
            c.exposure.allocation_id,
        ),
    )
    zone = ZoneInfo(policy.local_timezone)
    selections: list[CountBandSelection] = []
    quantities: list[QuoteQuantity] = []
    scenario = policy.interpretation_kind == "analyst_assumption"
    for case in ordered:
        exposure = case.exposure
        first = exposure.starts_at.astimezone(zone).date()
        last = (exposure.ends_at - timedelta(microseconds=1)).astimezone(zone).date()
        if len(case.facts) != len(rule.required_facts) or {
            f.fact_id for f in case.facts
        } != set(rule.required_facts):
            msg = "Supply exactly one fact for every required predicate"
            raise ValueError(msg)
        case_scenario = (
            policy.interpretation_kind == "analyst_assumption"
            or exposure.input_kind == "analyst_assumption"
        )
        for fact in case.facts:
            if (
                fact.known_on > policy.as_known_on
                or not fact.effective_from <= first <= last < fact.effective_to
            ):
                msg = "Count fact evidence lacks knowledge or whole-window coverage"
                raise ValueError(msg)
            case_scenario |= fact.input_kind == "analyst_assumption"
        scenario |= case_scenario
        bands = [b for b in rule.bands if b.minimum <= case.staff_count <= b.maximum]
        if len(bands) != 1:
            msg = "Exactly one explicit count band must cover the supplied count"
            raise ValueError(msg)
        band = bands[0]
        failed = tuple(sorted(f.fact_id for f in case.facts if not f.satisfied))
        quote = None
        amount = Fraction(0)
        if band.component is not None:
            matches = [
                q
                for q in release.quotes
                if q.component == band.component
                and q.unit == policy.unit
                and q.starts_on <= first <= last < q.ends_on
            ]
            if len(matches) != 1:
                msg = "Count band price must match component/unit and whole window"
                raise ValueError(msg)
            quote = matches[0]
            quantity = QuoteQuantity(
                quantity_id=exposure.allocation_id,
                quote_id=quote.quote_id,
                unit=policy.unit,
                quantity=Fraction(0) if failed else exposure.quantity,
                valued_on=exposure.valued_on,
                quantity_kind=(
                    "analyst_assumption" if case_scenario else "observed_use"
                ),
                basis=exposure.selection_basis,
            )
            quantities.append(quantity)
            amount = Fraction(quote.amount) * Fraction(quantity.quantity)
        selections.append(CountBandSelection(case, band, quote, failed, amount))
    return CountBandResult(
        "count_band_quotes_v1",
        rule,
        release,
        tuple(selections),
        scenario,
        price_units(release, tuple(quantities)),
    )
