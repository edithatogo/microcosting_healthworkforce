# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Price explicit units without inventing payroll calendars or conversions."""

from datetime import UTC, date, datetime
from decimal import Decimal, localcontext
from fractions import Fraction

import pytest

from src.source_registry import SourceRegistry
from src.unit_quotes import (
    QuoteQuantity,
    UnitQuote,
    UnitQuoteRelease,
    price_location_pool,
    price_units,
)
from tests.checks import assert_that
from tests.test_source_registry import source


def quote(**changes: object) -> UnitQuote:
    """Use synthetic independently quoted annual and period amounts."""
    values: dict[str, object] = {
        "quote_id": "period-1",
        "component": "development",
        "unit": "fortnight",
        "amount": Decimal("100.01"),
        "starts_on": date(2026, 1, 1),
        "ends_on": date(2027, 1, 1),
        "known_from": date(2026, 1, 1),
        "source_id": "synthetic-award-1",
        "source_sha256": "a" * 64,
        "citation": "Synthetic table row 1, fortnight column",
        "status": "accepted",
    }
    values.update(changes)
    return UnitQuote.model_validate(values)


def release(*quotes: UnitQuote) -> UnitQuoteRelease:
    """Freeze synthetic reviewed scope, knowledge date and quote set."""
    return UnitQuoteRelease(
        release_id="synthetic-1",
        currency="AUD",
        as_known_on=date(2026, 2, 1),
        jurisdiction="QLD",
        employer="Synthetic employer",
        classification="Synthetic grade",
        sources=SourceRegistry(records=(source(),)),
        quotes=quotes or (quote(),),
    )


def quantity(**changes: object) -> QuoteQuantity:
    """Require a deliberate valuation date and quantity provenance."""
    values: dict[str, object] = {
        "quantity_id": "event-1",
        "quote_id": "period-1",
        "unit": "fortnight",
        "quantity": Decimal(1),
        "valued_on": date(2026, 2, 1),
        "quantity_kind": "analyst_assumption",
        "basis": "One explicitly selected period price scenario",
    }
    values.update(changes)
    return QuoteQuantity.model_validate(values)


def test_independent_units_are_not_annualised() -> None:
    """Choose the exact source column; no fixed number of fortnights is assumed."""
    rates = release(
        quote(),
        quote(quote_id="annual-1", unit="annum", amount=Decimal(2700)),
    )
    period = price_units(rates, (quantity(),))
    annual = price_units(rates, (quantity(quote_id="annual-1", unit="annum"),))
    assert_that(period.total == Fraction(10001, 100))
    assert_that(annual.total == Fraction(2700))
    assert_that(period.total * 26 != annual.total)
    assert_that(period.rows[0].quote.quote_id == "period-1")
    assert_that(
        period.release_sha256 == price_units(rates, (quantity(),)).release_sha256,
    )


def test_dated_events_select_explicit_versions_and_exclusive_boundary() -> None:
    """A rate change affects later events, without spreading earlier quantities."""
    rates = release(
        quote(ends_on=date(2026, 7, 1)),
        quote(
            quote_id="period-2",
            starts_on=date(2026, 7, 1),
            amount=Decimal("110.01"),
        ),
    )
    events = (
        quantity(valued_on=date(2026, 6, 30)),
        quantity(
            quantity_id="event-2",
            quote_id="period-2",
            valued_on=date(2026, 7, 1),
        ),
    )
    result = price_units(rates, events)
    assert_that(result.total == Fraction(10501, 50))
    assert_that(price_units(rates, tuple(reversed(events))).total == result.total)
    with pytest.raises(ValueError, match="date"):
        price_units(rates, (quantity(valued_on=date(2026, 7, 1)),))


def test_exact_fractional_quantities_do_not_depend_on_decimal_context() -> None:
    """Repeated small quantities preserve cents without premature rounding."""
    rates = release()
    events = tuple(
        quantity(quantity_id=f"event-{i}", quantity=Decimal("0.0037"))
        for i in range(37)
    )
    with localcontext() as ctx:
        ctx.prec = 3
        result = price_units(rates, events)
    assert_that(result.total == Fraction(10001, 100) * Fraction(37, 10000) * 37)
    assert_that(sum((row.cost for row in result.rows), Fraction(0)) == result.total)


@pytest.mark.parametrize(
    "changes",
    [{"unit": "annum"}, {"quote_id": "absent"}, {"valued_on": date(2027, 1, 1)}],
)
def test_zero_quantities_still_require_unit_identity_and_date(
    changes: dict[str, object],
) -> None:
    """Zero must not hide unsupported scope or a missing quoted unit."""
    with pytest.raises(ValueError, match=r"unit|identity|date"):
        price_units(release(), (quantity(quantity=Decimal(0), **changes),))


def test_duplicate_events_are_rejected_and_empty_input_is_explicit_zero() -> None:
    """Duplicate quantity identities cannot silently double count."""
    rates = release()
    with pytest.raises(ValueError, match="Duplicate"):
        price_units(rates, (quantity(), quantity()))
    assert_that(price_units(rates, ()).total == 0)


@pytest.mark.parametrize(
    "changes",
    [
        {"status": "candidate"},
        {"source_sha256": "b" * 64},
        {"known_from": date(2026, 3, 1)},
        {"ends_on": date(2027, 1, 2)},
    ],
)
def test_release_rejects_unqualified_prices(changes: dict[str, object]) -> None:
    """Source scope/horizon/hash and knowledge date apply before pricing."""
    with pytest.raises(ValueError, match=r"accepted|hash|scope"):
        release(quote(**changes))


def test_overlapping_versions_and_model_copy_bypass_are_rejected() -> None:
    """Revalidation protects the runtime from unchecked copied objects."""
    with pytest.raises(ValueError, match="Overlapping"):
        release(quote(), quote(quote_id="duplicate-period"))
    rates = release().model_copy(update={"employer": "Other employer"})
    with pytest.raises(ValueError, match="scope"):
        price_units(rates, (quantity(),))
    bad = quantity().model_copy(update={"quantity": Decimal("NaN")})
    with pytest.raises(ValueError, match="finite"):
        price_units(release(), (bad,))


@pytest.mark.parametrize(
    "changes",
    [
        {"unit": " "},
        {"basis": " "},
        {"quantity": Decimal(-1)},
        {"quantity_kind": "inferred_entitlement"},
    ],
)
def test_quantity_requires_explicit_valid_units_and_provenance(
    changes: dict[str, object],
) -> None:
    """No implicit entitlement or unit can enter the quantity ledger."""
    with pytest.raises(ValueError, match=r"blank|greater|quantity_kind"):
        quantity(**changes)


def test_duplicate_quote_and_invalid_interval_are_rejected() -> None:
    """A price identity and bounded operative interval must be unambiguous."""
    with pytest.raises(ValueError, match="Duplicate"):
        release(quote(), quote())
    with pytest.raises(ValueError, match="nonempty"):
        quote(ends_on=date(2026, 1, 1))


def test_unresolved_source_and_future_retrieval_are_rejected() -> None:
    """The release cannot admit a candidate source or evidence acquired later."""
    rates = release()
    for record, expected in [
        (source(applicability="unresolved"), "scope"),
        (source(retrieved_at=datetime(2026, 3, 1, tzinfo=UTC)), "retrieval"),
    ]:
        changed = rates.model_dump()
        changed["sources"] = SourceRegistry(records=(record,)).model_dump()
        with pytest.raises(ValueError, match=expected):
            UnitQuoteRelease.model_validate(changed)


def test_release_hash_changes_with_price_and_quantity_retains_basis() -> None:
    """The receipt identifies the frozen price release and original input facts."""
    first = price_units(release(), (quantity(),))
    second = price_units(release(quote(amount=Decimal("100.02"))), (quantity(),))
    assert_that(first.release_sha256 != second.release_sha256)
    assert_that(first.rows[0].quantity.basis == quantity().basis)
    assert_that(first.rows[0].quote.source_sha256 == "a" * 64)


def test_exact_rational_quantity_is_preserved_through_json_and_pricing() -> None:
    """A derived nonterminating quantity must not be rounded to Decimal first."""
    data = quantity(quantity=Fraction(2100, 73))
    restored = QuoteQuantity.model_validate_json(data.model_dump_json())
    assert_that(restored.quantity == Fraction(2100, 73))
    with localcontext() as ctx:
        ctx.prec = 3
        result = price_units(release(), (restored,))
    assert_that(result.total == Fraction(210021, 73))
    assert_that(result.rows[0].quantity.quantity == Fraction(2100, 73))


@pytest.mark.parametrize("value", [Fraction(-1, 3), 0.5, True])
def test_rational_extension_preserves_strict_nonnegative_quantity_admission(
    value: object,
) -> None:
    """Neither negative rationals nor implicit float/bool conversions are valid."""
    with pytest.raises(ValueError, match=r"greater|instance|Decimal"):
        quantity(quantity=value)


def test_rational_zero_denominator_json_and_unchecked_float_fail() -> None:
    """Malformed rational strings and copied floats cannot bypass strict admission."""
    data = quantity(quantity=Fraction(1, 3))
    with pytest.raises(ValueError, match=r"fraction|Fraction|decimal"):
        QuoteQuantity.model_validate_json(
            data.model_dump_json().replace('"1/3"', '"1/0"'),
        )
    copied = quantity().model_copy(update={"quantity": 0.5})
    with pytest.raises(ValueError, match=r"instance|Decimal"):
        price_units(release(), (copied,))


def test_location_pool_preserves_exact_total_and_rejects_overallocation() -> None:
    """A complete reviewed cohort shares one price at a single date."""
    first = quantity(quantity=Fraction(1, 3))
    second = quantity(quantity_id="event-2", quantity=Fraction(2, 3))
    result = price_location_pool(release(), (first, second))
    assert_that(result.total == Fraction("100.01"))
    assert_that(result.rows[0].cost == Fraction("100.01") / 3)
    for invalid in (
        (first,),
        (first, second, quantity(quantity_id="event-3")),
        (first, second.model_copy(update={"valued_on": date(2026, 2, 2)})),
    ):
        with pytest.raises(ValueError, match="Location pool"):
            price_location_pool(release(), invalid)
