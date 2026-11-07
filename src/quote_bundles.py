# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Compare complete alternatives while retaining their separate source prices."""

from dataclasses import dataclass
from datetime import timedelta
from fractions import Fraction
from typing import Self
from zoneinfo import ZoneInfo

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


class QuoteBundleDefinition(QuoteModel):
    """Every required component of a comparison alternative."""

    alternative: str
    components: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def distinct_components(self) -> Self:
        """Reject duplicate and blank component identities."""
        if len(set(self.components)) != len(self.components) or any(
            not name.strip() for name in self.components
        ):
            msg = "Bundle components must be distinct and nonblank"
            raise ValueError(msg)
        return self


class QuoteBundleRule(QuoteModel):
    """Reviewed comparability and complete composition of the alternatives."""

    comparison: HighestQuoteRule
    bundles: tuple[QuoteBundleDefinition, ...] = Field(min_length=2)

    @model_validator(mode="after")
    def complete_definitions(self) -> Self:
        """Require exactly one definition per declared alternative."""
        names = [bundle.alternative for bundle in self.bundles]
        if len(set(names)) != len(names) or set(names) != set(
            self.comparison.selection.components,
        ):
            msg = "Supply exactly one bundle definition for each policy alternative"
            raise ValueError(msg)
        return self


class QuoteBundleFacts(QuoteModel):
    """Known eligibility for each required component of one alternative."""

    alternative: str
    facts: tuple[QuoteEligibility, ...] = Field(min_length=1)


class QuoteBundleCase(QuoteModel):
    """One shared explicit quantity and exposure window."""

    exposure: QuoteExposureWindow
    alternatives: tuple[QuoteBundleFacts, ...] = Field(min_length=2)


@dataclass(frozen=True)
class PricedQuoteBundle:
    """Retain component facts and quotes, including known-negative bundles."""

    definition: QuoteBundleDefinition
    facts: QuoteBundleFacts
    quotes: tuple[UnitQuote, ...]
    unit_total: Fraction | None
    prices: UnitQuoteResult | None


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
                    },
                )
                for bundle in case.alternatives
            ),
        },
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
    resolved = tuple(
        resolve_quote_eligibility(fact, policy, by_id, first, last)
        for fact in facts.facts
    )
    quotes = tuple(quote for quote in resolved if quote is not None)
    if len(quotes) != len(definition.components):
        return PricedQuoteBundle(definition, facts, quotes, None, None)
    scenario = (
        policy.interpretation_kind == "analyst_assumption"
        or case.exposure.input_kind == "analyst_assumption"
        or any(fact.input_kind == "analyst_assumption" for fact in facts.facts)
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
    return PricedQuoteBundle(
        definition,
        facts,
        quotes,
        sum((Fraction(quote.amount) for quote in quotes), Fraction(0)),
        price_units(release, quantities),
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
        totals = [
            bundle.unit_total for bundle in priced if bundle.unit_total is not None
        ]
        maximum = max(totals, default=None)
        winners = tuple(
            bundle.definition.alternative
            for bundle in priced
            if bundle.unit_total is not None and bundle.unit_total == maximum
        )
        selected = winners[0] if winners else None
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
