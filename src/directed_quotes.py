# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Directed allowance exclusions from complete pre-interaction eligibility facts."""

from dataclasses import dataclass
from datetime import timedelta
from typing import Literal, Self
from zoneinfo import ZoneInfo

from pydantic import Field, model_validator

from src.exclusive_quotes import (
    ExclusiveQuoteRule,
    QuoteExposureWindow,
    validate_quote_exposures,
)
from src.highest_quotes import QuoteEligibility
from src.unit_quotes import (
    QuoteModel,
    QuoteQuantity,
    UnitQuote,
    UnitQuoteRelease,
    UnitQuoteResult,
    price_units,
)


class QuoteExclusion(QuoteModel):
    """An eligible trigger bars a named entitlement, irrespective of its price."""

    trigger: str
    excluded: str
    citation: str


class DirectedQuoteRule(QuoteModel):
    """Reviewed same-unit scope and explicit acyclic entitlement exclusions."""

    scope: ExclusiveQuoteRule
    exclusions: tuple[QuoteExclusion, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_edges(self) -> Self:
        """Reject unknown, duplicate, self-referential or circular exclusions."""
        names = set(self.scope.components)
        edges = {(e.trigger, e.excluded) for e in self.exclusions}
        if len(edges) != len(self.exclusions) or any(
            a == b or a not in names or b not in names for a, b in edges
        ):
            msg = "Exclusions require distinct known components and unique edges"
            raise ValueError(msg)
        pending = set(names)
        while pending:
            roots = {
                n for n in pending if not any(b == n and a in pending for a, b in edges)
            }
            if not roots:
                msg = "Directed exclusions cannot contain a cycle"
                raise ValueError(msg)
            pending -= roots
        return self


class DirectedQuoteCase(QuoteModel):
    """Complete facts before exclusions for one independently qualified window."""

    exposure: QuoteExposureWindow
    alternatives: tuple[QuoteEligibility, ...] = Field(min_length=2)


@dataclass(frozen=True)
class SuppressedQuote:
    """Retain the otherwise eligible price and every directly eligible blocker."""

    quote: UnitQuote
    excluded_by: tuple[str, ...]


@dataclass(frozen=True)
class DirectedQuoteSelection:
    """All eligible, suppressed and paid prices for an auditable case."""

    case: DirectedQuoteCase
    eligible_quotes: tuple[UnitQuote, ...]
    suppressed: tuple[SuppressedQuote, ...]
    paid_quote_ids: tuple[str, ...]


@dataclass(frozen=True)
class DirectedQuoteResult:
    """Exact prices and retained zero/selection evidence without inferred facts."""

    rule: DirectedQuoteRule
    selections: tuple[DirectedQuoteSelection, ...]
    scenario: bool
    prices: UnitQuoteResult
    method_id: Literal["eligible_facts_directed_exclusions_v1"] = (
        "eligible_facts_directed_exclusions_v1"
    )


def price_directed_quotes(
    rule: DirectedQuoteRule,
    release: UnitQuoteRelease,
    cases: tuple[DirectedQuoteCase, ...],
) -> DirectedQuoteResult:
    """Exclude targets of eligible triggers, then add every surviving quote once.

    Eligibility is the complete pre-interaction predicate: an eligible trigger
    still excludes its direct targets if another edge suppresses its own payment.
    No transitive edges, maximum selection, entitlement inference or cross-unit
    conversion is added. Every positive quote, including suppressed quotes, must
    cover the complete supplied window. Relevant rate/policy changes require splits.
    """
    scope = ExclusiveQuoteRule.model_validate(dict(rule.scope))
    rule = DirectedQuoteRule.model_validate(
        dict(rule)
        | {
            "scope": scope,
            "exclusions": tuple(
                QuoteExclusion.model_validate(dict(e)) for e in rule.exclusions
            ),
        },
    )
    release = UnitQuoteRelease.model_validate(release.model_dump())
    rebuilt = tuple(
        DirectedQuoteCase.model_validate(
            dict(c)
            | {
                "exposure": QuoteExposureWindow.model_validate(dict(c.exposure)),
                "alternatives": tuple(
                    QuoteEligibility.model_validate(dict(a)) for a in c.alternatives
                ),
            },
        )
        for c in cases
    )
    validate_quote_exposures(scope, release, tuple(c.exposure for c in rebuilt))
    zone = ZoneInfo(scope.local_timezone)
    by_id = {q.quote_id: q for q in release.quotes}
    quantities: list[QuoteQuantity] = []
    selections: list[DirectedQuoteSelection] = []
    scenario = scope.interpretation_kind == "analyst_assumption"
    for case in sorted(
        rebuilt,
        key=lambda c: (c.exposure.resource_id, c.exposure.starts_at),
    ):
        exposure = case.exposure
        if len(case.alternatives) != len(scope.components) or {
            a.component for a in case.alternatives
        } != set(scope.components):
            msg = "Supply exactly one pre-interaction fact for every component"
            raise ValueError(msg)
        first = exposure.starts_at.astimezone(zone).date()
        last = (exposure.ends_at - timedelta(microseconds=1)).astimezone(zone).date()
        eligible: dict[str, UnitQuote] = {}
        case_scenario = (
            scope.interpretation_kind == "analyst_assumption"
            or exposure.input_kind == "analyst_assumption"
        )
        for fact in case.alternatives:
            if fact.known_on > scope.as_known_on or (
                fact.input_kind == "observed_case_evidence" and fact.known_on < last
            ):
                msg = "Component evidence exceeds knowledge or predates its window"
                raise ValueError(msg)
            case_scenario |= fact.input_kind == "analyst_assumption"
            if not fact.eligible:
                continue
            quote = by_id.get(fact.quote_id or "")
            if (
                quote is None
                or quote.component != fact.component
                or quote.unit != scope.unit
                or not quote.starts_on <= first <= last < quote.ends_on
            ):
                msg = "Every eligible quote must match component/unit and whole window"
                raise ValueError(msg)
            eligible[fact.component] = quote
        suppressed: list[SuppressedQuote] = []
        paid: list[str] = []
        for name, quote in sorted(eligible.items()):
            blockers = tuple(
                sorted(
                    e.trigger
                    for e in rule.exclusions
                    if e.excluded == name and e.trigger in eligible
                ),
            )
            if blockers:
                suppressed.append(SuppressedQuote(quote, blockers))
                continue
            paid.append(quote.quote_id)
            quantities.append(
                QuoteQuantity(
                    quantity_id=f"{len(exposure.allocation_id)}:{exposure.allocation_id}{name}",
                    quote_id=quote.quote_id,
                    unit=scope.unit,
                    quantity=exposure.quantity,
                    valued_on=exposure.valued_on,
                    quantity_kind=(
                        "analyst_assumption" if case_scenario else "observed_use"
                    ),
                    basis=exposure.selection_basis,
                ),
            )
        scenario |= case_scenario
        selections.append(
            DirectedQuoteSelection(
                case,
                tuple(q for _, q in sorted(eligible.items())),
                tuple(suppressed),
                tuple(paid),
            ),
        )
    return DirectedQuoteResult(
        rule,
        tuple(selections),
        scenario,
        price_units(release, tuple(quantities)),
    )
