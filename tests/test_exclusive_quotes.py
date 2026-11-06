# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Source-qualified alternatives cannot overlap a resource exposure."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, localcontext
from fractions import Fraction
from zoneinfo import ZoneInfo

import pytest

from src.exclusive_quotes import (
    ExclusiveQuoteAllocation,
    ExclusiveQuoteRule,
    price_exclusive_quotes,
)
from tests.checks import assert_that
from tests.test_crib_away import release


def rule(**changes: object) -> ExclusiveQuoteRule:
    """Provide a fictional reviewed exclusive group against existing test prices."""
    values: dict[str, object] = {
        "rule_id": "synthetic-exclusive-policy",
        "components": ("single_context", "two_context"),
        "unit": "directed_crib_occasion",
        "local_timezone": "Australia/Sydney",
        "source_id": "synthetic-award-1",
        "source_sha256": "a" * 64,
        "citation": "Synthetic alternative rule",
        "reviewed": True,
        "interpretation_kind": "source_reviewed",
        "interpretation_basis": "Synthetic context and window qualification",
        "effective_from": date(2026, 5, 15),
        "effective_to": date(2026, 11, 8),
        "as_known_on": date(2026, 11, 7),
        "jurisdiction": "QLD",
        "employer": "Synthetic employer",
        "classification": "Synthetic grade",
    }
    values.update(changes)
    return ExclusiveQuoteRule.model_validate(values)


def allocation(**changes: object) -> ExclusiveQuoteAllocation:
    """Supply an explicitly eligible independent window and chosen quote."""
    values: dict[str, object] = {
        "allocation_id": "exposure-1",
        "resource_id": "opaque-resource",
        "starts_at": datetime(2026, 7, 10, 7, tzinfo=ZoneInfo("Australia/Sydney")),
        "ends_at": datetime(2026, 7, 10, 19, tzinfo=ZoneInfo("Australia/Sydney")),
        "valued_on": date(2026, 7, 10),
        "quote_id": "single_context-2026",
        "quantity": Decimal(1),
        "eligibility_verified": True,
        "history_complete": True,
        "selection_basis": "Synthetic independently qualified window/context",
        "input_kind": "observed_case_evidence",
        "evidence_id": "synthetic-evidence",
        "evidence_sha256": "b" * 64,
        "known_on": date(2026, 11, 7),
    }
    values.update(changes)
    return ExclusiveQuoteAllocation.model_validate(values)


def test_snapshot_keeps_distinct_resources_and_never_selects_maximum() -> None:
    """The cheaper explicitly chosen context remains selected for its own worker."""
    a = allocation()
    b = allocation(
        allocation_id="exposure-2",
        resource_id="other",
        quote_id="two_context-2026",
    )
    result = price_exclusive_quotes(rule(), release(), (b, a))
    assert_that(result.prices.total == Fraction(413, 25))
    assert_that(not result.scenario)
    assert_that(result.allocations == (a, b))
    assert_that(result.rule.citation == "Synthetic alternative rule")


def test_dated_events_use_distinct_prices_without_inferred_quantity() -> None:
    """Adjacent explicit periods may switch context/price; fractions stay exact."""
    a = allocation(
        starts_at=datetime(2026, 7, 9, tzinfo=UTC),
        ends_at=datetime(2026, 7, 9, 1, tzinfo=UTC),
        valued_on=date(2026, 7, 9),
        quote_id="single_context-2025",
        quantity=Fraction(1, 3),
    )
    b = allocation(allocation_id="new", quantity=Fraction(2, 3))
    with localcontext() as context:
        context.prec = 2
        result = price_exclusive_quotes(rule(), release(), (a, b))
    assert_that(result.prices.total == Fraction(3203, 300))
    assert_that(result.allocations[0].quantity == Fraction(1, 3))


@pytest.mark.parametrize("offset", [0, 1, 11])
def test_overlapping_alternative_windows_rejected(offset: int) -> None:
    """Changing context or identity cannot pay two overlapping alternatives."""
    a = allocation()
    b = allocation(
        allocation_id="different-id",
        starts_at=a.starts_at + timedelta(hours=offset),
        ends_at=a.ends_at + timedelta(hours=offset),
        quote_id="two_context-2026",
    )
    with pytest.raises(ValueError, match="overlap"):
        price_exclusive_quotes(rule(), release(), (a, b))


def test_adjacent_windows_allowed_without_elapsed_hour_entitlement() -> None:
    """Half-open windows share an endpoint without overlap or automatic proration."""
    a = allocation()
    b = allocation(
        allocation_id="adjacent",
        starts_at=a.ends_at,
        ends_at=a.ends_at + timedelta(minutes=1),
        quote_id="two_context-2026",
    )
    result = price_exclusive_quotes(rule(), release(), (a, b))
    assert_that(result.prices.total == Fraction(413, 25))


@pytest.mark.parametrize(
    "changes",
    [
        {"quantity": Decimal(-1)},
        {"quantity": True},
        {"quantity": Decimal("NaN")},
        {"eligibility_verified": False},
        {"history_complete": False},
        {"selection_basis": " "},
        {"evidence_id": " "},
        {"evidence_sha256": "wrong"},
        {"starts_at": datetime(2026, 7, 10, tzinfo=UTC).replace(tzinfo=None)},
        {"ends_at": datetime(2026, 7, 10, 7, tzinfo=ZoneInfo("Australia/Sydney"))},
    ],
)
def test_forged_allocations_revalidated(changes: dict[str, object]) -> None:
    """Unchecked model_copy must not bypass input invariants."""
    forged = allocation().model_copy(update=changes)
    with pytest.raises(
        ValueError,
        match=r"quantity|Allocation|selection_basis|evidence_|timezone",
    ):
        price_exclusive_quotes(rule(), release(), (forged,))


@pytest.mark.parametrize(
    "changes",
    [
        {"components": ("single_context", "single_context")},
        {"components": ("single_context", " ")},
        {"reviewed": False},
        {"effective_to": date(2026, 5, 15)},
        {"source_sha256": "c" * 64},
        {"employer": "different employer"},
        {"as_known_on": date(2026, 11, 6)},
        {"unit": "hour"},
        {"components": ("unrelated-a", "unrelated-b")},
        {"source_id": "absent"},
    ],
)
def test_forged_policy_scope_hash_and_alternatives_rejected(
    changes: dict[str, object],
) -> None:
    """Each policy is independently source-qualified rather than trusting prices."""
    forged = rule().model_copy(update=changes)
    with pytest.raises(
        ValueError,
        match=r"policy|Policy|Selected alternative|Source|source",
    ):
        price_exclusive_quotes(forged, release(), (allocation(),))


@pytest.mark.parametrize(
    "changes",
    [
        {"quote_id": "absent"},
        {"known_on": date(2026, 11, 8)},
        {"known_on": date(2026, 7, 9)},
        {"valued_on": date(2026, 7, 11)},
        {"quote_id": "single_context-2025"},
        {"ends_at": datetime(2026, 11, 8, 1, tzinfo=ZoneInfo("Australia/Sydney"))},
        {"starts_at": datetime(2026, 7, 9, tzinfo=ZoneInfo("Australia/Sydney"))},
    ],
)
def test_dates_and_quote_cover_whole_window(changes: dict[str, object]) -> None:
    """Valuation date alone cannot hide a policy, price or evidence boundary."""
    with pytest.raises(ValueError, match=r"Selected alternative|Allocation dates"):
        price_exclusive_quotes(rule(), release(), (allocation(**changes),))


def test_unknown_and_duplicate_allocations_do_not_become_zero() -> None:
    """A known zero has a qualified complete window; missing history has none."""
    for values in [(), (allocation(), allocation())]:
        with pytest.raises(ValueError, match="nonempty allocation set with unique"):
            price_exclusive_quotes(rule(), release(), values)
    result = price_exclusive_quotes(
        rule(),
        release(),
        (allocation(quantity=Decimal(0)),),
    )
    assert_that(result.prices.total == 0)
    assert_that(len(result.prices.rows) == 1)


def test_assumptions_are_explicit_and_never_relabelled_observed() -> None:
    """Either policy interpretation or case assumptions mark the result scenario."""
    a = allocation(input_kind="analyst_assumption", known_on=date(2026, 1, 1))
    assert_that(price_exclusive_quotes(rule(), release(), (a,)).scenario)
    assert_that(
        price_exclusive_quotes(
            rule(interpretation_kind="analyst_assumption"),
            release(),
            (allocation(),),
        ).scenario,
    )


def test_dst_window_uses_instants_without_deriving_unit_quantity() -> None:
    """A calendar day with23elapsed hours can carry one explicit unit unchanged."""
    a = allocation(
        starts_at=datetime(2026, 10, 4, tzinfo=ZoneInfo("Australia/Sydney")),
        ends_at=datetime(2026, 10, 5, tzinfo=ZoneInfo("Australia/Sydney")),
        valued_on=date(2026, 10, 4),
    )
    result = price_exclusive_quotes(rule(), release(), (a,))
    assert_that(result.prices.total == Fraction(1101, 100))
    assert_that(a.ends_at - a.starts_at == timedelta(hours=23))
