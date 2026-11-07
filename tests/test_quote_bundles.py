# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Synthetic composed alternatives retain exact component-level evidence."""

from datetime import date, timedelta
from decimal import Decimal, localcontext
from fractions import Fraction

import pytest

from src.highest_quotes import HighestQuoteRule
from src.quote_bundles import (
    QuoteBundleCase,
    QuoteBundleDefinition,
    QuoteBundleFacts,
    QuoteBundleRule,
    price_highest_quote_bundles,
)
from src.unit_quotes import UnitQuoteRelease
from tests.checks import assert_that
from tests.test_crib_away import release
from tests.test_exclusive_quotes import rule
from tests.test_highest_quotes import case, fact


def bundle_rule() -> QuoteBundleRule:
    """Declare complete same-period alternatives independently of their prices."""
    return QuoteBundleRule(
        comparison=HighestQuoteRule(
            selection=rule(components=("combined", "single"), unit="pay_period"),
            comparability_reviewed=True,
            comparability_basis="Fictional complete comparable wage alternatives",
        ),
        bundles=(
            QuoteBundleDefinition(
                alternative="combined",
                components=("two_context", "incentive"),
            ),
            QuoteBundleDefinition(alternative="single", components=("single_context",)),
        ),
    )


def bundle_release(incentive: str = "6") -> UnitQuoteRelease:
    """Supply distinct source prices for base, incentive and alternative base."""
    original = release()
    quotes = tuple(q.model_copy(update={"unit": "pay_period"}) for q in original.quotes)
    extra = next(q for q in quotes if q.quote_id == "two_context-2026").model_copy(
        update={
            "quote_id": "incentive-2026",
            "component": "incentive",
            "amount": Decimal(incentive),
        },
    )
    return UnitQuoteRelease.model_validate(
        {**original.model_dump(), "quotes": (*quotes, extra)},
    )


def bundle_case() -> QuoteBundleCase:
    """Require a fact for every component of each declared alternative."""
    return QuoteBundleCase(
        exposure=case().exposure,
        alternatives=(
            QuoteBundleFacts(
                alternative="combined",
                facts=(fact("two_context"), fact("incentive")),
            ),
            QuoteBundleFacts(alternative="single", facts=(fact("single_context"),)),
        ),
    )


def test_composed_winner_retains_components_and_pays_once() -> None:
    """5.51 plus 6 exceeds 11.01 without also paying the losing salary."""
    result = price_highest_quote_bundles(
        bundle_rule(),
        bundle_release(),
        (bundle_case(),),
    )
    selected = result.selections[0]
    assert_that(selected.selected_alternative == "combined")
    assert_that(selected.winning_alternatives == ("combined",))
    assert_that(result.prices.total == Fraction(1151, 100))
    assert_that(
        [row.quote.component for row in result.prices.rows]
        == [
            "two_context",
            "incentive",
        ],
    )
    assert_that(selected.alternatives[1].unit_total == Fraction(1101, 100))
    assert_that(not result.scenario)


def test_ties_zero_quantity_and_fractional_exactness() -> None:
    """Tie choice is deterministic and based on unit totals even at zero use."""
    c = bundle_case()
    zero = c.model_copy(
        update={
            "exposure": c.exposure.model_copy(
                update={"quantity": Fraction(0)},
            ),
        },
    )
    result = price_highest_quote_bundles(bundle_rule(), bundle_release("5.5"), (zero,))
    assert_that(result.selections[0].winning_alternatives == ("combined", "single"))
    assert_that(result.prices.total == 0)
    fractional = c.model_copy(
        update={
            "exposure": c.exposure.model_copy(
                update={"quantity": Fraction(1, 3)},
            ),
        },
    )
    with localcontext() as context:
        context.prec = 2
        exact = price_highest_quote_bundles(
            bundle_rule(),
            bundle_release(),
            (fractional,),
        )
    assert_that(exact.prices.total == Fraction(1151, 300))


def test_negative_component_disqualifies_whole_bundle() -> None:
    """An incentive exclusion cannot silently turn a bundle into a smaller offer."""
    c = bundle_case()
    combined = c.alternatives[0].model_copy(
        update={
            "facts": (
                fact("two_context"),
                fact("incentive", eligible=False, quote_id=None),
            ),
        },
    )
    result = price_highest_quote_bundles(
        bundle_rule(),
        bundle_release(),
        (c.model_copy(update={"alternatives": (combined, c.alternatives[1])}),),
    )
    assert_that(result.selections[0].selected_alternative == "single")
    assert_that(result.selections[0].alternatives[0].unit_total is None)
    assert_that(result.prices.total == Fraction(1101, 100))


def test_missing_facts_and_unknown_alternatives_fail() -> None:
    """Unknown eligibility and incomplete composition cannot become zero prices."""
    c = bundle_case()
    missing = c.alternatives[0].model_copy(update={"facts": (fact("two_context"),)})
    with pytest.raises(ValueError, match="every bundle component"):
        price_highest_quote_bundles(
            bundle_rule(),
            bundle_release(),
            (c.model_copy(update={"alternatives": (missing, c.alternatives[1])}),),
        )
    unknown = c.alternatives[0].model_copy(update={"alternative": "unknown"})
    with pytest.raises(ValueError, match="policy alternative"):
        price_highest_quote_bundles(
            bundle_rule(),
            bundle_release(),
            (c.model_copy(update={"alternatives": (unknown, c.alternatives[1])}),),
        )


def test_known_all_negative_retains_zero_and_overlaps_fail() -> None:
    """Zero requires complete negative facts and exposures cannot be repeated."""
    c = bundle_case()
    negatives = tuple(
        b.model_copy(
            update={
                "facts": tuple(
                    f.model_copy(update={"eligible": False, "quote_id": None})
                    for f in b.facts
                ),
            },
        )
        for b in c.alternatives
    )
    result = price_highest_quote_bundles(
        bundle_rule(),
        bundle_release(),
        (c.model_copy(update={"alternatives": negatives}),),
    )
    assert_that(result.prices.total == 0)
    assert_that(result.selections[0].selected_alternative is None)
    duplicate = c.model_copy(
        update={
            "exposure": c.exposure.model_copy(
                update={"allocation_id": "second"},
            ),
        },
    )
    with pytest.raises(ValueError, match="overlap"):
        price_highest_quote_bundles(bundle_rule(), bundle_release(), (c, duplicate))


def test_component_unit_and_whole_window_must_match() -> None:
    """Valuation-date coverage alone is insufficient for a multi-day bundle."""
    c = bundle_case()
    original = bundle_release()
    wrong = original.model_copy(
        update={
            "quotes": tuple(
                q.model_copy(update={"unit": "hour"})
                if q.component == "incentive"
                else q
                for q in original.quotes
            ),
        },
    )
    with pytest.raises(ValueError, match="component/unit and whole window"):
        price_highest_quote_bundles(bundle_rule(), wrong, (c,))
    expiring = original.model_copy(
        update={
            "quotes": tuple(
                q.model_copy(update={"ends_on": date(2026, 7, 11)})
                if q.component == "incentive"
                else q
                for q in original.quotes
            ),
        },
    )
    extended = c.model_copy(
        update={
            "exposure": c.exposure.model_copy(
                update={"ends_at": c.exposure.ends_at + timedelta(days=1)},
            ),
        },
    )
    with pytest.raises(ValueError, match="whole window"):
        price_highest_quote_bundles(bundle_rule(), expiring, (extended,))


def test_revalidates_nested_copies_and_definition_completeness() -> None:
    """Copied models cannot bypass eligibility or comparison review."""
    c = bundle_case()
    malformed = c.alternatives[0].facts[0].model_copy(update={"quote_id": None})
    alternative = c.alternatives[0].model_copy(
        update={
            "facts": (malformed, c.alternatives[0].facts[1]),
        },
    )
    with pytest.raises(ValueError, match="Eligible alternatives"):
        price_highest_quote_bundles(
            bundle_rule(),
            bundle_release(),
            (c.model_copy(update={"alternatives": (alternative, c.alternatives[1])}),),
        )
    policy = bundle_rule()
    unreviewed = policy.model_copy(
        update={
            "comparison": policy.comparison.model_copy(
                update={"comparability_reviewed": False},
            ),
        },
    )
    with pytest.raises(ValueError, match="reviewed comparability"):
        price_highest_quote_bundles(unreviewed, bundle_release(), (c,))
    with pytest.raises(ValueError, match="bundle definition"):
        QuoteBundleRule(
            comparison=policy.comparison,
            bundles=(policy.bundles[0], policy.bundles[0]),
        )
