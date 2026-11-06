# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Require complete comparable alternatives before selecting one maximum."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, localcontext
from fractions import Fraction

import pytest

from src.exclusive_quotes import QuoteExposureWindow
from src.highest_quotes import (
    HighestQuoteCase,
    HighestQuoteRule,
    QuoteEligibility,
    price_highest_quotes,
)
from tests.checks import assert_that
from tests.test_crib_away import release
from tests.test_exclusive_quotes import allocation, rule


def policy() -> HighestQuoteRule:
    """Declare fictional same-unit comparability explicitly."""
    return HighestQuoteRule(
        selection=rule(),
        comparability_reviewed=True,
        comparability_basis="Synthetic same-nature same-unit allowance group",
    )


def fact(component: str, **changes: object) -> QuoteEligibility:
    """Retain known eligibility independently for every group component."""
    values: dict[str, object] = {
        "component": component,
        "eligible": True,
        "quote_id": component + "-2026",
        "basis": "Synthetic reviewed fact",
        "input_kind": "observed_case_evidence",
        "known_on": date(2026, 11, 7),
        "evidence_id": component + "-fact",
        "evidence_sha256": "b" * 64,
    }
    values.update(changes)
    return QuoteEligibility.model_validate(values)


def case(**changes: object) -> HighestQuoteCase:
    """Use an upstream-qualified exposure without asking the caller for a winner."""
    a = allocation()
    exposure = QuoteExposureWindow.model_validate(
        {k: v for k, v in dict(a).items() if k != "quote_id"},
    )
    values: dict[str, object] = {
        "exposure": exposure,
        "alternatives": (fact("single_context"), fact("two_context")),
    }
    values.update(changes)
    return HighestQuoteCase.model_validate(values)


def test_selects_one_maximum_and_retains_loser() -> None:
    """The maximum rate is paid once rather than summed with a lower alternative."""
    result = price_highest_quotes(policy(), release(), (case(),))
    selected = result.selections[0]
    assert_that(result.prices.total == Fraction(1101, 100))
    assert_that(selected.selected_quote_id == "single_context-2026")
    assert_that(len(selected.eligible_quotes) == len(policy().selection.components))
    assert_that(selected.winning_quote_ids == ("single_context-2026",))
    assert_that(not result.scenario)


def test_ineligible_larger_price_does_not_win() -> None:
    """Eligibility is reviewed separately from the numeric comparison."""
    c = case(
        alternatives=(
            fact("single_context", eligible=False, quote_id=None),
            fact("two_context"),
        ),
    )
    result = price_highest_quotes(policy(), release(), (c,))
    assert_that(result.prices.total == Fraction(551, 100))
    assert_that(result.selections[0].selected_quote_id == "two_context-2026")


def test_known_all_negative_is_retained_zero() -> None:
    """A complete qualified negative set differs from unknown or absent inputs."""
    c = case(
        alternatives=tuple(
            fact(name, eligible=False, quote_id=None)
            for name in policy().selection.components
        ),
    )
    result = price_highest_quotes(policy(), release(), (c,))
    assert_that(result.prices.total == 0)
    assert_that(len(result.selections) == 1)
    assert_that(result.selections[0].selected_quote_id is None)
    assert_that(result.selections[0].eligible_quotes == ())
    assert_that(result.prices.rows == ())


def test_ties_are_retained_but_paid_once_deterministically() -> None:
    """All winning IDs remain visible and input order does not affect payment."""
    r = release()
    quotes = tuple(q.model_copy(update={"amount": Decimal("11.01")}) for q in r.quotes)
    r = r.model_copy(update={"quotes": quotes})
    a = case()
    b = case(alternatives=tuple(reversed(a.alternatives)))
    first = price_highest_quotes(policy(), r, (a,))
    second = price_highest_quotes(policy(), r, (b,))
    assert_that(first.prices.total == Fraction(1101, 100) == second.prices.total)
    assert_that(
        first.selections[0].winning_quote_ids
        == (
            "single_context-2026",
            "two_context-2026",
        ),
    )
    assert_that(
        first.selections[0].selected_quote_id == second.selections[0].selected_quote_id,
    )


def test_dated_maxima_and_fractional_units_are_exact() -> None:
    """Each explicitly split window selects its own price without annual conversion."""
    now = case()
    earlier = now.exposure.model_copy(
        update={
            "allocation_id": "older",
            "starts_at": datetime(2026, 7, 9, tzinfo=UTC),
            "ends_at": datetime(2026, 7, 9, 1, tzinfo=UTC),
            "valued_on": date(2026, 7, 9),
            "quantity": Fraction(1, 3),
        },
    )
    old = case(
        exposure=earlier,
        alternatives=tuple(
            fact(name, quote_id=name + "-2025")
            for name in policy().selection.components
        ),
    )
    with localcontext() as context:
        context.prec = 2
        result = price_highest_quotes(policy(), release(), (now, old))
    assert_that(result.prices.total == Fraction(4304, 300))
    assert_that(result.selections[0].selected_quote_id == "single_context-2025")


@pytest.mark.parametrize(
    "alternatives",
    [
        (),
        (fact("single_context"),),
        (fact("single_context"), fact("single_context")),
        (fact("single_context"), fact("unknown")),
    ],
)
def test_incomplete_or_duplicate_fact_sets_fail(
    alternatives: tuple[QuoteEligibility, ...],
) -> None:
    """Omitting a competing condition cannot manufacture the largest eligible rate."""
    forged = case().model_copy(update={"alternatives": alternatives})
    with pytest.raises(ValueError, match=r"at least 2|every declared alternative"):
        price_highest_quotes(policy(), release(), (forged,))


@pytest.mark.parametrize(
    "changes",
    [
        {"eligible": None},
        {"eligible": 1},
        {"eligible": False},
        {"quote_id": None},
        {"quote_id": "two_context-2026"},
        {"quote_id": "missing"},
        {"known_on": date(2026, 11, 8)},
        {"known_on": date(2026, 7, 9)},
        {"basis": " "},
        {"evidence_sha256": "bad"},
    ],
)
def test_forged_choice_facts_revalidated(changes: dict[str, object]) -> None:
    """Unchecked copies cannot hide an unknown, future, mismatched or invalid fact."""
    c = case().model_copy(
        update={
            "alternatives": (
                fact("single_context").model_copy(update=changes),
                fact("two_context"),
            ),
        },
    )
    with pytest.raises(
        ValueError,
        match=r"eligible|quote|evidence|basis|knowledge|Quote fields",
    ):
        price_highest_quotes(policy(), release(), (c,))


def test_losing_quote_must_cover_the_complete_window_and_unit() -> None:
    """A disqualified losing alternative makes the comparison incomplete."""
    r = release()
    for change in [{"unit": "other-unit"}, {"ends_on": date(2026, 7, 11)}]:
        quotes = tuple(
            q.model_copy(update=change) if q.quote_id == "two_context-2026" else q
            for q in r.quotes
        )
        with pytest.raises(ValueError, match="Every eligible quote"):
            price_highest_quotes(
                policy(),
                r.model_copy(update={"quotes": quotes}),
                (
                    case(
                        exposure=case().exposure.model_copy(
                            update={
                                "ends_at": datetime(2026, 7, 12, tzinfo=UTC),
                            },
                        ),
                    ),
                ),
            )


def test_unknown_windows_and_overlaps_rejected_even_for_all_negative() -> None:
    """Zero alternatives do not bypass resource history or policy validation."""
    c = case(
        alternatives=tuple(
            fact(name, eligible=False, quote_id=None)
            for name in policy().selection.components
        ),
    )
    duplicate = c.model_copy(
        update={
            "exposure": c.exposure.model_copy(
                update={
                    "allocation_id": "overlapping",
                },
            ),
        },
    )
    for cases in [(), (c, c), (c, duplicate)]:
        with pytest.raises(ValueError, match=r"nonempty|overlap"):
            price_highest_quotes(policy(), release(), cases)
    forged = c.model_copy(
        update={
            "exposure": c.exposure.model_copy(
                update={
                    "history_complete": False,
                },
            ),
        },
    )
    with pytest.raises(ValueError, match="qualified eligibility/history"):
        price_highest_quotes(policy(), release(), (forged,))


def test_policy_review_scope_and_hash_apply_to_negative_cases() -> None:
    """No price selected does not mean policy evidence can be omitted."""
    p = policy()
    c = case(
        alternatives=tuple(
            fact(name, eligible=False, quote_id=None) for name in p.selection.components
        ),
    )
    with pytest.raises(ValueError, match="reviewed comparability"):
        price_highest_quotes(
            p.model_copy(update={"comparability_reviewed": False}),
            release(),
            (c,),
        )
    for change in [{"source_sha256": "c" * 64}, {"employer": "different"}]:
        forged = p.model_copy(
            update={"selection": p.selection.model_copy(update=change)},
        )
        with pytest.raises(ValueError, match=r"matching held hash|matching scope"):
            price_highest_quotes(forged, release(), (c,))


def test_case_assumptions_do_not_relabel_other_observed_rows() -> None:
    """A scenario flag propagates without corrupting per-row evidence kinds."""
    a = case()
    b = case(
        exposure=a.exposure.model_copy(
            update={
                "allocation_id": "other",
                "resource_id": "second-resource",
                "input_kind": "analyst_assumption",
            },
        ),
    )
    for first, second in [(a, b), (b, a)]:
        result = price_highest_quotes(policy(), release(), (first, second))
        kinds = {
            r.quantity.quantity_id: r.quantity.quantity_kind for r in result.prices.rows
        }
        assert_that(result.scenario)
        assert_that(
            kinds == {"exposure-1": "observed_use", "other": "analyst_assumption"},
        )


def test_negative_fact_assumption_marks_the_comparison_scenario() -> None:
    """Retain an assumed exclusion even when the selected price is observed."""
    c = case(
        alternatives=(
            fact("single_context"),
            fact(
                "two_context",
                eligible=False,
                quote_id=None,
                input_kind="analyst_assumption",
                known_on=date(2026, 1, 1),
            ),
        ),
    )
    result = price_highest_quotes(policy(), release(), (c,))
    assert_that(result.scenario)
    assert_that(result.prices.rows[0].quantity.quantity_kind == "analyst_assumption")


def test_window_boundary_coverage_is_preserved() -> None:
    """Keep shared window coverage checks effective for the comparison."""
    c = case()
    exposure = c.exposure.model_copy(
        update={
            "ends_at": c.exposure.ends_at + timedelta(days=130),
        },
    )
    with pytest.raises(ValueError, match="policy/knowledge coverage"):
        price_highest_quotes(
            policy(),
            release(),
            (c.model_copy(update={"exposure": exposure}),),
        )


def test_forged_outer_case_extra_fields_are_rejected() -> None:
    """Preserve the outer strict schema while rebuilding nested unchecked inputs."""
    forged = case().model_copy(update={"unknown_basis": "unreviewed"})
    with pytest.raises(ValueError, match="Extra inputs are not permitted"):
        price_highest_quotes(policy(), release(), (forged,))
