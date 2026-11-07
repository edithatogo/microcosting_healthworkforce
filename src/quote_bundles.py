# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Compare complete alternatives while retaining their separate source prices."""

from dataclasses import dataclass
from datetime import date, timedelta
from fractions import Fraction
from typing import Self
from zoneinfo import ZoneInfo
lazy from decimal import Decimal

from pydantic import Field, model_validator

from src.exclusive_quotes import QuoteExposureWindow, validate_quote_exposures
from src.highest_quotes import (
    HighestQuoteRule,
    QuoteEligibility,
    resolve_quote_eligibility,
)
from src.unit_quotes import (
    QuoteModel,
    QuoteQuantity,
    UnitQuote,
    UnitQuoteRelease,
    UnitQuoteResult,
    price_units,
)


class QuoteBundlePercentage(QuoteModel):
    """Reviewed percentage of a separately identified same-unit basis quote."""

    component: str
    basis_component: str
    fraction: Decimal = Field(ge=0, allow_inf_nan=False)
    source_id: str
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation: str
    starts_on: date
    ends_on: date
    known_from: date
    reviewed: bool

    @model_validator(mode="after")
    def reviewed_window(self) -> Self:
        """Require review and a nonempty rule window."""
        if not self.reviewed or self.ends_on <= self.starts_on:
            msg = "Percentage component requires review and a nonempty window"
            raise ValueError(msg)
        return self


class QuoteBundleDefinition(QuoteModel):
    """Every required component of a comparison alternative."""

    alternative: str
    components: tuple[str, ...] = Field(min_length=1)
    percentage: QuoteBundlePercentage | None = None

    @model_validator(mode="after")
    def distinct_components(self) -> Self:
        """Reject duplicate and blank component identities."""
        if len(set(self.components)) != len(self.components) or any(
            not name.strip() for name in self.components
        ):
            msg = "Bundle components must be distinct and nonblank"
            raise ValueError(msg)
        if self.percentage is not None and self.percentage.component in self.components:
            msg = "Percentage component must be distinct from paid direct components"
            raise ValueError(msg)
        return self


class QuoteBundleRule(QuoteModel):
    """Reviewed comparability and complete composition of the alternatives."""

    comparison: HighestQuoteRule
    bundles: tuple[QuoteBundleDefinition, ...] = Field(min_length=2)
    tie_priority: tuple[str, ...] | None = None

    @model_validator(mode="after")
    def complete_definitions(self) -> Self:
        """Require exactly one definition per declared alternative."""
        names = [bundle.alternative for bundle in self.bundles]
        if len(set(names)) != len(names) or set(names) != set(
            self.comparison.selection.components,
        ):
            msg = "Supply exactly one bundle definition for each policy alternative"
            raise ValueError(msg)
        if self.tie_priority is not None and (
            len(self.tie_priority) != len(names) or set(self.tie_priority) != set(names)
        ):
            msg = "Tie priority must list each alternative exactly once"
            raise ValueError(msg)
        return self


class QuoteBundleFacts(QuoteModel):
    """Known eligibility for each required component of one alternative."""

    alternative: str
    facts: tuple[QuoteEligibility, ...] = Field(min_length=1)
    percentage_basis: QuoteEligibility | None = None


class QuoteBundleCase(QuoteModel):
    """One shared explicit quantity and exposure window."""

    exposure: QuoteExposureWindow
    alternatives: tuple[QuoteBundleFacts, ...] = Field(min_length=2)


@dataclass(frozen=True)
class PricedBundlePercentage:
    """Separate calculation lineage from the direct payment ledger."""

    rule: QuoteBundlePercentage
    basis_quote: UnitQuote
    unit_amount: Fraction
    cost: Fraction


@dataclass(frozen=True)
class PricedQuoteBundle:
    """Retain component facts and quotes, including known-negative bundles."""

    definition: QuoteBundleDefinition
    facts: QuoteBundleFacts
    quotes: tuple[UnitQuote, ...]
    unit_total: Fraction | None
    prices: UnitQuoteResult | None
    percentage: PricedBundlePercentage | None = None


@dataclass(frozen=True)
class QuoteBundleSelection:
    """Retain all comparisons, ties and the deterministic single paid option."""

    case: QuoteBundleCase
    alternatives: tuple[PricedQuoteBundle, ...]
    winning_alternatives: tuple[str, ...]
    selected_alternative: str | None


@dataclass(frozen=True)
class QuoteBundleResult:
    """Keep source component payments separate from comparison metadata."""

    rule: QuoteBundleRule
    selections: tuple[QuoteBundleSelection, ...]
    scenario: bool
    prices: UnitQuoteResult
    method_id: str = "highest_comparable_quote_bundle_v1"

    @property
    def paid_percentages(self) -> tuple[PricedBundlePercentage, ...]:
        """Return percentage rows from the selected alternatives only."""
        return tuple(
            bundle.percentage
            for selection in self.selections
            for bundle in selection.alternatives
            if bundle.definition.alternative == selection.selected_alternative
            and bundle.percentage is not None
        )

    @property
    def total(self) -> Fraction:
        """Return exact selected direct and percentage amounts together."""
        return self.prices.total + sum(
            (row.cost for row in self.paid_percentages),
            Fraction(0),
        )


def _rebuild_case(case: QuoteBundleCase) -> QuoteBundleCase:
    """Revalidate nested models while preserving Fraction quantities."""
    return QuoteBundleCase.model_validate(
        dict(case)
        | {
            "exposure": QuoteExposureWindow.model_validate(dict(case.exposure)),
            "alternatives": tuple(
                QuoteBundleFacts.model_validate(
                    dict(bundle)
                    | {
                        "facts": tuple(
                            QuoteEligibility.model_validate(dict(fact))
                            for fact in bundle.facts
                        ),
                        "percentage_basis": (
                            QuoteEligibility.model_validate(
                                dict(bundle.percentage_basis),
                            )
                            if bundle.percentage_basis is not None
                            else None
                        ),
                    },
                )
                for bundle in case.alternatives
            ),
        },
    )


def _percentage_basis(
    definition: QuoteBundleDefinition,
    facts: QuoteBundleFacts,
    rule: QuoteBundleRule,
    release: UnitQuoteRelease,
    window: tuple[date, date],
) -> UnitQuote | None:
    """Check whole-window policy and the explicitly asserted allowance basis."""
    percentage = definition.percentage
    fact = facts.percentage_basis
    if percentage is None and fact is None:
        return None
    if (
        percentage is None
        or fact is None
        or fact.component != percentage.basis_component
    ):
        msg = "Supply the declared percentage basis fact"
        raise ValueError(msg)
    first, last = window
    if (
        not percentage.starts_on <= first <= last < percentage.ends_on
        or percentage.known_from > release.as_known_on
    ):
        msg = "Percentage rule must cover the whole window and knowledge date"
        raise ValueError(msg)
    for day in (first, last):
        source = release.sources.require_applicable(
            percentage.source_id,
            day,
            release.jurisdiction,
            release.employer,
            release.classification,
        )
        if (
            source.sha256 != percentage.source_sha256
            or source.retrieved_at is None
            or source.retrieved_at.date() > release.as_known_on
        ):
            msg = "Percentage rule source must match the held and known edition"
            raise ValueError(msg)
    by_id = {quote.quote_id: quote for quote in release.quotes}
    return resolve_quote_eligibility(
        fact,
        rule.comparison.selection,
        by_id,
        first,
        last,
    )


def _price_bundle(
    rule: QuoteBundleRule,
    release: UnitQuoteRelease,
    case: QuoteBundleCase,
    definition: QuoteBundleDefinition,
    identity: int,
) -> PricedQuoteBundle:
    """Require every fact and price the complete eligible component set."""
    facts = next(
        bundle
        for bundle in case.alternatives
        if bundle.alternative == definition.alternative
    )
    if len(facts.facts) != len(definition.components) or {
        fact.component for fact in facts.facts
    } != set(definition.components):
        msg = "Supply exactly one eligibility fact for every bundle component"
        raise ValueError(msg)
    policy = rule.comparison.selection
    zone = ZoneInfo(policy.local_timezone)
    first = case.exposure.starts_at.astimezone(zone).date()
    last = (case.exposure.ends_at - timedelta(microseconds=1)).astimezone(zone).date()
    by_id = {quote.quote_id: quote for quote in release.quotes}
    basis = _percentage_basis(definition, facts, rule, release, (first, last))
    resolved = tuple(
        resolve_quote_eligibility(fact, policy, by_id, first, last)
        for fact in facts.facts
    )
    quotes = tuple(quote for quote in resolved if quote is not None)
    if len(quotes) != len(definition.components) or (
        definition.percentage is not None and basis is None
    ):
        return PricedQuoteBundle(definition, facts, quotes, None, None)
    scenario = (
        policy.interpretation_kind == "analyst_assumption"
        or case.exposure.input_kind == "analyst_assumption"
        or any(fact.input_kind == "analyst_assumption" for fact in facts.facts)
        or (
            facts.percentage_basis is not None
            and facts.percentage_basis.input_kind == "analyst_assumption"
        )
    )
    quantities = tuple(
        QuoteQuantity(
            quantity_id=f"bundle-{identity}-part-{index}",
            quote_id=quote.quote_id,
            unit=policy.unit,
            quantity=case.exposure.quantity,
            valued_on=case.exposure.valued_on,
            quantity_kind="analyst_assumption" if scenario else "observed_use",
            basis=case.exposure.selection_basis,
        )
        for index, quote in enumerate(quotes)
    )
    unit_total = sum((Fraction(quote.amount) for quote in quotes), Fraction(0))
    percentage = None
    if definition.percentage is not None and basis is not None:
        unit_amount = Fraction(basis.amount) * Fraction(definition.percentage.fraction)
        percentage = PricedBundlePercentage(
            definition.percentage,
            basis,
            unit_amount,
            unit_amount * Fraction(case.exposure.quantity),
        )
        unit_total += unit_amount
    return PricedQuoteBundle(
        definition,
        facts,
        quotes,
        unit_total,
        price_units(release, quantities),
        percentage,
    )


def price_highest_quote_bundles(
    rule: QuoteBundleRule,
    release: UnitQuoteRelease,
    cases: tuple[QuoteBundleCase, ...],
) -> QuoteBundleResult:
    """Pay one maximum complete same-unit bundle for each supplied exposure.

    Composition, comparability, eligibility and quantities are reviewed inputs.
    Split relevant rate changes and reconcile any existing salary ledger before
    combining results.
    """
    rule = QuoteBundleRule.model_validate(rule.model_dump())
    release = UnitQuoteRelease.model_validate(release.model_dump())
    cases = tuple(_rebuild_case(case) for case in cases)
    validate_quote_exposures(
        rule.comparison.selection,
        release,
        tuple(case.exposure for case in cases),
    )
    definitions = {bundle.alternative: bundle for bundle in rule.bundles}
    tie_priority = rule.tie_priority or tuple(sorted(definitions))
    selections: list[QuoteBundleSelection] = []
    quantities: list[QuoteQuantity] = []
    scenario = rule.comparison.selection.interpretation_kind == "analyst_assumption"
    for index, case in enumerate(cases):
        facts = {bundle.alternative: bundle for bundle in case.alternatives}
        if len(facts) != len(case.alternatives) or set(facts) != set(definitions):
            msg = "Supply exactly one fact bundle for every policy alternative"
            raise ValueError(msg)
        priced = tuple(
            _price_bundle(
                rule,
                release,
                case,
                definition,
                index * len(definitions) + offset,
            )
            for offset, (_name, definition) in enumerate(sorted(definitions.items()))
        )
        scenario |= case.exposure.input_kind == "analyst_assumption" or any(
            fact.input_kind == "analyst_assumption"
            for bundle in case.alternatives
            for fact in bundle.facts
        )
        scenario |= any(
            bundle.percentage_basis is not None
            and bundle.percentage_basis.input_kind == "analyst_assumption"
            for bundle in case.alternatives
        )
        totals = [
            bundle.unit_total for bundle in priced if bundle.unit_total is not None
        ]
        maximum = max(totals, default=None)
        winners = tuple(
            bundle.definition.alternative
            for bundle in priced
            if bundle.unit_total is not None and bundle.unit_total == maximum
        )
        selected = next((name for name in tie_priority if name in winners), None)
        selections.append(QuoteBundleSelection(case, priced, winners, selected))
        for bundle in priced:
            if bundle.definition.alternative == selected and bundle.prices is not None:
                quantities.extend(row.quantity for row in bundle.prices.rows)
    return QuoteBundleResult(
        rule,
        tuple(selections),
        scenario,
        price_units(release, tuple(quantities)),
    )
