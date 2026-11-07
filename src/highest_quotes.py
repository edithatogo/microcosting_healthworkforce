# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Highest-only pricing of complete reviewed comparable allowance alternatives."""

from dataclasses import dataclass
from datetime import date, timedelta
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


class HighestQuoteRule(QuoteModel):
    """Reviewed same-unit comparability, separate from occupational eligibility."""

    selection: ExclusiveQuoteRule
    comparability_reviewed: bool
    comparability_basis: str

    @model_validator(mode="after")
    def reviewed_comparison(self) -> Self:
        """Require a reviewed grouping independently of the numeric maximum."""
        if not self.comparability_reviewed:
            msg = "Highest comparison requires reviewed comparability"
            raise ValueError(msg)
        return self


class QuoteEligibility(QuoteModel):
    """One known positive or negative fact for a declared alternative."""

    component: str
    eligible: bool
    quote_id: str | None
    basis: str
    input_kind: Literal["observed_case_evidence", "analyst_assumption"]
    known_on: date
    evidence_id: str
    evidence_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def eligibility_quote(self) -> Self:
        """Only eligible alternatives select a quote; unknown is not false."""
        if self.eligible != (self.quote_id is not None):
            msg = "Eligible alternatives require a quote; negative facts must omit it"
            raise ValueError(msg)
        return self


class HighestQuoteCase(QuoteModel):
    """A complete alternative set for one independently qualified exposure."""

    exposure: QuoteExposureWindow
    alternatives: tuple[QuoteEligibility, ...] = Field(min_length=2)


@dataclass(frozen=True)
class HighestQuoteSelection:
    """Retain eligible losers, all ties and the deterministic single paid choice."""

    case: HighestQuoteCase
    eligible_quotes: tuple[UnitQuote, ...]
    winning_quote_ids: tuple[str, ...]
    selected_quote_id: str | None


@dataclass(frozen=True)
class HighestQuoteResult:
    """Exact non-cumulative results, including explicit all-negative zero cases."""

    rule: HighestQuoteRule
    selections: tuple[HighestQuoteSelection, ...]
    scenario: bool
    prices: UnitQuoteResult
    method_id: Literal["highest_comparable_unit_quote_v1"] = (
        "highest_comparable_unit_quote_v1"
    )


def resolve_quote_eligibility(
    fact: QuoteEligibility,
    policy: ExclusiveQuoteRule,
    by_id: dict[str, UnitQuote],
    first: date,
    last: date,
) -> UnitQuote | None:
    """Resolve a complete known fact against a whole comparable window."""
    if fact.known_on > policy.as_known_on or (
        fact.input_kind == "observed_case_evidence" and fact.known_on < last
    ):
        msg = "Alternative evidence exceeds knowledge or predates its window"
        raise ValueError(msg)
    if not fact.eligible:
        return None
    quote = by_id.get(fact.quote_id or "")
    if (
        quote is None
        or quote.component != fact.component
        or quote.unit != policy.unit
        or not quote.starts_on <= first <= last < quote.ends_on
    ):
        msg = "Every eligible quote must match component/unit and whole window"
        raise ValueError(msg)
    return quote


def price_highest_quotes(
    rule: HighestQuoteRule,
    release: UnitQuoteRelease,
    cases: tuple[HighestQuoteCase, ...],
) -> HighestQuoteResult:
    """Pay one maximum comparable rate for each supplied eligible exposure window.

    Every declared component needs an explicit eligibility fact. Same-nature
    grouping, resource history, quantity allocation and policy precedence remain
    reviewed inputs. No conversion across units, automatic time proration, rolling
    cap or whole-period maximum is inferred. Split every relevant rate change.
    """
    policy = ExclusiveQuoteRule.model_validate(dict(rule.selection))
    rule = HighestQuoteRule.model_validate(dict(rule) | {"selection": policy})
    release = UnitQuoteRelease.model_validate(release.model_dump())
    rebuilt = tuple(
        HighestQuoteCase.model_validate(
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
    validate_quote_exposures(policy, release, tuple(c.exposure for c in rebuilt))
    ordered = sorted(
        rebuilt,
        key=lambda c: (c.exposure.resource_id, c.exposure.starts_at),
    )
    zone = ZoneInfo(policy.local_timezone)
    by_id = {q.quote_id: q for q in release.quotes}
    selections: list[HighestQuoteSelection] = []
    quantities: list[QuoteQuantity] = []
    scenario = policy.interpretation_kind == "analyst_assumption"
    for case in ordered:
        exposure = case.exposure
        first = exposure.starts_at.astimezone(zone).date()
        last = (exposure.ends_at - timedelta(microseconds=1)).astimezone(zone).date()
        if len(case.alternatives) != len(policy.components) or {
            a.component for a in case.alternatives
        } != set(policy.components):
            msg = "Supply exactly one eligibility fact for every declared alternative"
            raise ValueError(msg)
        eligible: list[UnitQuote] = []
        case_scenario = (
            policy.interpretation_kind == "analyst_assumption"
            or exposure.input_kind == "analyst_assumption"
        )
        for fact in case.alternatives:
            case_scenario |= fact.input_kind == "analyst_assumption"
            quote = resolve_quote_eligibility(fact, policy, by_id, first, last)
            if quote is not None:
                eligible.append(quote)
        scenario |= case_scenario
        eligible.sort(key=lambda q: q.quote_id)
        maximum = max((q.amount for q in eligible), default=None)
        winners = tuple(q.quote_id for q in eligible if q.amount == maximum)
        chosen = winners[0] if winners else None
        selections.append(HighestQuoteSelection(case, tuple(eligible), winners, chosen))
        if chosen is not None:
            quantities.append(
                QuoteQuantity(
                    quantity_id=exposure.allocation_id,
                    quote_id=chosen,
                    unit=policy.unit,
                    quantity=exposure.quantity,
                    valued_on=exposure.valued_on,
                    quantity_kind=(
                        "analyst_assumption" if case_scenario else "observed_use"
                    ),
                    basis=exposure.selection_basis,
                ),
            )
    return HighestQuoteResult(
        rule,
        tuple(selections),
        scenario,
        price_units(release, tuple(quantities)),
    )
