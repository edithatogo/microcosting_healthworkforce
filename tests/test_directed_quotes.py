# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Directed entitlement exclusions are independent of which price is highest."""

from datetime import UTC, date, datetime
from decimal import Decimal, localcontext
from fractions import Fraction

import pytest

from src.directed_quotes import (
    DirectedQuoteCase,
    DirectedQuoteRule,
    QuoteExclusion,
    price_directed_quotes,
)
from tests.checks import assert_that
from tests.test_crib_away import release
from tests.test_exclusive_quotes import rule
from tests.test_highest_quotes import case, fact
lazy from src.unit_quotes import UnitQuoteRelease

TWO_COMPONENTS = 2


def policy() -> DirectedQuoteRule:
    """Declare a lower-price entitlement that excludes a higher-price one."""
    return DirectedQuoteRule(
        scope=rule(),
        exclusions=(
            QuoteExclusion(
                trigger="two_context",
                excluded="single_context",
                citation="Synthetic would-otherwise-be-payable clause",
            ),
        ),
    )


def exposure_case() -> DirectedQuoteCase:
    """Reuse complete fictional eligibility and source-qualified windows."""
    c = case()
    return DirectedQuoteCase(exposure=c.exposure, alternatives=c.alternatives)


def test_lower_price_entitlement_excludes_higher_price() -> None:
    """Priority follows a reviewed directed edge rather than a numeric maximum."""
    result = price_directed_quotes(policy(), release(), (exposure_case(),))
    assert_that(result.prices.total == Fraction(551, 100))
    assert_that(result.selections[0].paid_quote_ids == ("two_context-2026",))
    assert_that(
        result.selections[0].suppressed[0].quote.quote_id == "single_context-2026",
    )
    assert_that(result.selections[0].suppressed[0].excluded_by == ("two_context",))
    assert_that(not result.scenario)


def test_ineligible_trigger_does_not_block_target() -> None:
    """Known-negative trigger leaves the otherwise eligible target payable."""
    c = exposure_case().model_copy(
        update={
            "alternatives": (
                fact("single_context"),
                fact("two_context", eligible=False, quote_id=None),
            ),
        },
    )
    result = price_directed_quotes(policy(), release(), (c,))
    assert_that(result.prices.total == Fraction(1101, 100))
    assert_that(result.selections[0].suppressed == ())


def test_known_all_negative_is_retained_zero() -> None:
    """An explicitly known empty entitlement set retains its input evidence."""
    c = exposure_case().model_copy(
        update={
            "alternatives": tuple(
                fact(n, eligible=False, quote_id=None)
                for n in policy().scope.components
            ),
        },
    )
    result = price_directed_quotes(policy(), release(), (c,))
    assert_that(result.prices.total == 0)
    assert_that(result.prices.rows == ())
    assert_that(result.selections[0].case == c)
    assert_that(result.selections[0].paid_quote_ids == ())


def third_case() -> tuple[DirectedQuoteRule, UnitQuoteRelease, DirectedQuoteCase]:
    """Add an independent eligible component to exercise additive survivors."""
    p = policy()
    p = p.model_copy(
        update={
            "scope": p.scope.model_copy(
                update={"components": (*p.scope.components, "other")},
            ),
        },
    )
    r = release()
    quote = r.quotes[-1].model_copy(
        update={"quote_id": "other-2026", "component": "other", "amount": Decimal(7)},
    )
    r = r.model_copy(update={"quotes": (*r.quotes, quote)})
    c = exposure_case()
    c = c.model_copy(update={"alternatives": (*c.alternatives, fact("other"))})
    return p, r, c


def test_unrelated_survivors_are_added_not_maximised() -> None:
    """A directed edge excludes only its named target, preserving other extras."""
    p, r, c = third_case()
    result = price_directed_quotes(p, r, (c,))
    assert_that(result.prices.total == Fraction(1251, 100))
    assert_that(
        result.selections[0].paid_quote_ids == ("other-2026", "two_context-2026"),
    )
    assert_that(
        len({row.quantity.quantity_id for row in result.prices.rows}) == TWO_COMPONENTS,
    )


def test_suppressed_but_eligible_trigger_still_blocks_its_direct_target() -> None:
    """Would-otherwise predicates are evaluated before payment suppression."""
    p, r, c = third_case()
    extra = QuoteExclusion(
        trigger="single_context",
        excluded="other",
        citation="Synthetic second directed predicate",
    )
    p = p.model_copy(update={"exclusions": (*p.exclusions, extra)})
    result = price_directed_quotes(p, r, (c,))
    assert_that(result.prices.total == Fraction(551, 100))
    assert_that(len(result.selections[0].suppressed) == TWO_COMPONENTS)


def test_no_automatic_transitive_exclusion_when_middle_predicate_negative() -> None:
    """An edge chain does not create an absent A-to-C rule."""
    p, r, c = third_case()
    p = p.model_copy(
        update={
            "exclusions": (
                *p.exclusions,
                QuoteExclusion(
                    trigger="single_context",
                    excluded="other",
                    citation="Synthetic second directed predicate",
                ),
            ),
        },
    )
    c = c.model_copy(
        update={
            "alternatives": (
                fact("single_context", eligible=False, quote_id=None),
                fact("two_context"),
                fact("other"),
            ),
        },
    )
    result = price_directed_quotes(p, r, (c,))
    assert_that(result.prices.total == Fraction(1251, 100))


@pytest.mark.parametrize(
    "edges",
    [
        (),
        (("two_context", "unknown"),),
        (("two_context", "two_context"),),
        (("two_context", "single_context"), ("two_context", "single_context")),
        (("two_context", "single_context"), ("single_context", "two_context")),
    ],
)
def test_invalid_graphs_fail_before_pricing(edges: tuple[tuple[str, str], ...]) -> None:
    """Unknown/self/duplicate/circular policy cannot silently eliminate costs."""
    p = policy().model_copy(
        update={
            "exclusions": tuple(
                QuoteExclusion(trigger=a, excluded=b, citation="Synthetic edge")
                for a, b in edges
            ),
        },
    )
    with pytest.raises(ValueError, match=r"Exclusions|cycle|at least 1"):
        price_directed_quotes(p, release(), (exposure_case(),))


def test_multiple_direct_blockers_and_order_are_retained() -> None:
    """Rule/fact ordering cannot change paid amounts or hide a blocker."""
    p, r, c = third_case()
    p = p.model_copy(
        update={
            "exclusions": (
                *p.exclusions,
                QuoteExclusion(
                    trigger="other",
                    excluded="single_context",
                    citation="Synthetic independent blocker",
                ),
            ),
        },
    )
    first = price_directed_quotes(p, r, (c,))
    second = price_directed_quotes(
        p.model_copy(update={"exclusions": tuple(reversed(p.exclusions))}),
        r,
        (c.model_copy(update={"alternatives": tuple(reversed(c.alternatives))}),),
    )
    assert_that(first.prices.total == second.prices.total == Fraction(1251, 100))
    assert_that(
        first.selections[0].suppressed[0].excluded_by == ("other", "two_context"),
    )
    assert_that(
        first.selections[0].paid_quote_ids == second.selections[0].paid_quote_ids,
    )


@pytest.mark.parametrize("duplicate", [False, True])
def test_missing_or_duplicate_facts_are_unknown_not_zero(*, duplicate: bool) -> None:
    """Every declared component requires exactly one explicit eligibility fact."""
    c = exposure_case()
    alternatives = (c.alternatives[0],) * (2 if duplicate else 1)
    with pytest.raises(ValueError, match=r"every component|at least 2"):
        price_directed_quotes(
            policy(),
            release(),
            (c.model_copy(update={"alternatives": alternatives}),),
        )


@pytest.mark.parametrize("change", ["unit", "window", "component", "missing"])
def test_suppressed_quote_still_requires_valid_price_coverage(change: str) -> None:
    """An exclusion cannot conceal an invalid otherwise-eligible quote."""
    r = release()
    c = exposure_case()
    if change == "missing":
        c = c.model_copy(
            update={
                "alternatives": (
                    fact("single_context", quote_id="absent"),
                    fact("two_context"),
                ),
            },
        )
    else:
        changes: dict[str, dict[str, object]] = {
            "unit": {"unit": "different-unit"},
            "window": {"starts_on": date(2026, 7, 11)},
            "component": {"component": "wrong-component"},
        }
        update = changes[change]
        r = r.model_copy(
            update={
                "quotes": tuple(
                    q.model_copy(update=update)
                    if q.quote_id == "single_context-2026"
                    else q
                    for q in r.quotes
                ),
            },
        )
    with pytest.raises(ValueError, match=r"quote|component|unit|window"):
        price_directed_quotes(policy(), r, (c,))


@pytest.mark.parametrize(
    "kind",
    ["rule", "exposure", "suppressed_fact", "negative_fact"],
)
def test_scenario_propagates_even_from_nonpaid_inputs(kind: str) -> None:
    """One analyst assumption marks all prices in its case and the overall result."""
    p = policy()
    c = exposure_case()
    if kind == "rule":
        p = p.model_copy(
            update={
                "scope": p.scope.model_copy(
                    update={"interpretation_kind": "analyst_assumption"},
                ),
            },
        )
    elif kind == "exposure":
        c = c.model_copy(
            update={
                "exposure": c.exposure.model_copy(
                    update={"input_kind": "analyst_assumption"},
                ),
            },
        )
    else:
        f = fact("single_context", input_kind="analyst_assumption")
        if kind == "negative_fact":
            f = f.model_copy(update={"eligible": False, "quote_id": None})
        c = c.model_copy(update={"alternatives": (f, fact("two_context"))})
    result = price_directed_quotes(p, release(), (c,))
    assert_that(result.scenario)
    assert_that(
        all(
            row.quantity.quantity_kind == "analyst_assumption"
            for row in result.prices.rows
        ),
    )


@pytest.mark.parametrize("known", [date(2026, 7, 9), date(2026, 11, 8)])
def test_component_evidence_dates_are_bounded(known: date) -> None:
    """Future knowledge and evidence preceding observed work both fail."""
    c = exposure_case().model_copy(
        update={
            "alternatives": (
                fact("single_context", known_on=known),
                fact("two_context"),
            ),
        },
    )
    with pytest.raises(ValueError, match=r"knowledge|predates"):
        price_directed_quotes(policy(), release(), (c,))


def test_policy_source_hash_and_nested_review_are_revalidated() -> None:
    """Forged frozen outer/nested copies do not bypass source or review checks."""
    p = policy()
    for changes in [{"source_sha256": "c" * 64}, {"reviewed": False}]:
        forged = p.model_copy(update={"scope": p.scope.model_copy(update=changes)})
        with pytest.raises(ValueError, match=r"review|hash"):
            price_directed_quotes(forged, release(), (exposure_case(),))


def test_overlapping_or_absent_windows_fail() -> None:
    """Complete allocation sets cannot double-price one resource's same window."""
    c = exposure_case()
    with pytest.raises(ValueError, match="nonempty"):
        price_directed_quotes(policy(), release(), ())
    other = c.model_copy(
        update={"exposure": c.exposure.model_copy(update={"allocation_id": "another"})},
    )
    with pytest.raises(ValueError, match="overlap"):
        price_directed_quotes(policy(), release(), (c, other))


def test_rational_quantity_roundtrip_and_decimal_precision() -> None:
    """The one-third quantity is exact through nested serialization and pricing."""
    c = exposure_case()
    c = c.model_copy(
        update={"exposure": c.exposure.model_copy(update={"quantity": Fraction(1, 3)})},
    )
    c = DirectedQuoteCase.model_validate_json(c.model_dump_json())
    p = DirectedQuoteRule.model_validate_json(policy().model_dump_json())
    with localcontext() as context:
        context.prec = 3
        result = price_directed_quotes(p, release(), (c,))
    assert_that(result.prices.total == Fraction(551, 300))


def test_dated_cases_switch_prices_without_splitting_entitlement_units() -> None:
    """Different declared nonoverlapping windows select their own whole-window quote."""
    c = exposure_case()
    early = c.model_copy(
        update={
            "exposure": c.exposure.model_copy(
                update={
                    "allocation_id": "earlier",
                    "starts_at": datetime(2026, 7, 9, tzinfo=UTC),
                    "ends_at": datetime(2026, 7, 9, 1, tzinfo=UTC),
                    "valued_on": date(2026, 7, 9),
                },
            ),
            "alternatives": tuple(
                fact(n, quote_id=n + "-2025") for n in policy().scope.components
            ),
        },
    )
    result = price_directed_quotes(policy(), release(), (c, early))
    assert_that(result.prices.total == Fraction(263, 25))
    assert_that(result.selections[0].paid_quote_ids == ("two_context-2025",))
