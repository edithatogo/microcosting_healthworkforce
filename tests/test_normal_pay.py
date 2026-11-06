# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Compose exact selected hours and explicitly supplied continuing allowances."""

from dataclasses import replace
from datetime import date
from decimal import Decimal, localcontext
from fractions import Fraction

import pytest

from src.historical_hours import NormalHoursSelection, select_normal_hours
from src.normal_pay import HoursPricingRequest, price_selected_hours
from src.source_registry import SourceRegistry
from tests.checks import assert_that
from tests.test_historical_hours import history, request, rule
from tests.test_source_registry import source
from tests.test_unit_quotes import quantity, quote, release
lazy from src.unit_quotes import QuoteQuantity, UnitQuote, UnitQuoteRelease


def selection() -> NormalHoursSelection:
    """Use the established synthetic exact historical-hours scenario."""
    return select_normal_hours(rule(), request(), (history(),))


def prices(*extras: UnitQuote) -> UnitQuoteRelease:
    """Use a salary-only hourly quote and separately declared allowance prices."""
    salary = quote(
        quote_id="salary",
        component="salary",
        unit="hour",
        amount=Decimal(30),
    )
    return release(salary, *extras).model_copy(
        update={"as_known_on": date(2026, 11, 7)},
    )


def exposure(**changes: object) -> HoursPricingRequest:
    """Select one explicit week without making an earned/payroll-period claim."""
    values: dict[str, object] = {
        "quantity_id": "selected-hours",
        "quote_id": "salary",
        "week_quantity": Fraction(1),
        "valued_on": date(2026, 11, 7),
        "basis": "Synthetic normal-hours price exposure scenario",
        "base_included_components": (),
        "exclusive_component_groups": (),
        "allowance_interaction_basis": "Synthetic separate allowance quantities",
        "base_inclusion_basis": "Synthetic salary-only quote",
    }
    values.update(changes)
    return HoursPricingRequest.model_validate(values)


def allowance(**changes: object) -> QuoteQuantity:
    """Supply a separate counterfactual allowance quantity and source unit."""
    return quantity(
        quantity_id="allowance",
        quote_id="development",
        unit="fortnight",
        quantity=Fraction(1, 2),
        valued_on=date(2026, 11, 7),
        **changes,
    )


def test_selected_hours_price_preserves_exact_fraction_and_lineage() -> None:
    """The selection-to-price bridge must not round a repeating weekly base."""
    selected = selection()
    with localcontext() as ctx:
        ctx.prec = 3
        result = price_selected_hours(prices(), selected, exposure(), ())
    assert_that(result.pricing.total == Fraction(63000, 73))
    assert_that(result.selection == selected)
    assert_that(result.pricing.rows[0].quantity.quantity == Fraction(2100, 73))
    assert_that(result.pricing.rows[0].quantity.unit == "hour")
    assert_that(result.request.base_inclusion_basis == exposure().base_inclusion_basis)


def test_separate_allowance_is_not_scaled_again_with_salary_hours() -> None:
    """A supplied fortnight quantity keeps its own price and denominator."""
    rates = prices(
        quote(
            quote_id="development",
            component="development",
            amount=Decimal("100.01"),
        ),
    )
    result = price_selected_hours(
        rates,
        selection(),
        exposure(week_quantity=Fraction(1, 2)),
        (allowance(),),
    )
    assert_that(result.pricing.rows[0].cost == Fraction(31500, 73))
    assert_that(result.pricing.rows[1].cost == Fraction(10001, 200))
    assert_that(result.pricing.total == Fraction(31500, 73) + Fraction(10001, 200))


def test_forged_derived_selection_is_recomputed_from_original_inputs() -> None:
    """A frozen dataclass is not a validation boundary for supplied totals."""
    forged = replace(selection(), selected_hours_per_week=Fraction(9999))
    result = price_selected_hours(prices(), forged, exposure(), ())
    assert_that(result.selection.selected_hours_per_week == Fraction(2100, 73))
    assert_that(result.pricing.total == Fraction(63000, 73))


@pytest.mark.parametrize("component", ["salary", "development"])
def test_base_inclusions_prevent_duplicate_allowance_charges(component: str) -> None:
    """Loaded base inclusions and the base component cannot be charged twice."""
    rates = prices(quote(quote_id="development", component=component))
    with pytest.raises(ValueError, match="included"):
        price_selected_hours(
            rates,
            selection(),
            exposure(base_included_components=("development",)),
            (allowance(),),
        )


def test_two_columns_for_the_same_allowance_are_not_summed() -> None:
    """Different units/identities do not make the same component additive."""
    rates = prices(
        quote(quote_id="development", component="development"),
        quote(quote_id="development-year", component="development", unit="annum"),
    )
    annual = quantity(
        quantity_id="annual",
        quote_id="development-year",
        unit="annum",
        valued_on=date(2026, 11, 7),
    )
    with pytest.raises(ValueError, match="Duplicate component"):
        price_selected_hours(rates, selection(), exposure(), (allowance(), annual))


def test_mixed_knowledge_or_scope_and_different_allowance_dates_fail() -> None:
    """One snapshot retains consistent scope and declared knowledge context."""
    with pytest.raises(ValueError, match="knowledge"):
        price_selected_hours(
            prices().model_copy(update={"as_known_on": date(2026, 2, 1)}),
            selection(),
            exposure(),
            (),
        )
    other = replace(
        selection(),
        rule=rule(
            classification="Different grade",
            sources=SourceRegistry(
                records=(source(classifications=("Different grade",)),),
            ),
        ),
    )
    with pytest.raises(ValueError, match="scope"):
        price_selected_hours(prices(), other, exposure(), ())
    rates = prices(quote(quote_id="development", component="development"))
    changed = allowance().model_copy(update={"valued_on": date(2026, 11, 8)})
    with pytest.raises(ValueError, match="snapshot"):
        price_selected_hours(rates, selection(), exposure(), (changed,))


@pytest.mark.parametrize(
    "changes",
    [
        {"week_quantity": Fraction(-1)},
        {"base_included_components": ("",)},
        {"base_included_components": ("a", "a")},
        {"base_inclusion_basis": " "},
    ],
)
def test_invalid_exposure_and_inclusion_declarations_fail(
    changes: dict[str, object],
) -> None:
    """No implicit included-component or negative-exposure defaults enter."""
    with pytest.raises(ValueError, match=r"greater|component|basis"):
        exposure(**changes)


def test_named_quote_units_and_duplicate_quantity_admission_remain_strict() -> None:
    """The adapter cannot turn an unknown/annual quote into an hourly price."""
    with pytest.raises(ValueError, match="No quote"):
        price_selected_hours(prices(), selection(), exposure(quote_id="absent"), ())
    missing = allowance().model_copy(update={"quote_id": "absent"})
    with pytest.raises(ValueError, match="No quote"):
        price_selected_hours(prices(), selection(), exposure(), (missing,))
    annual = release(quote(quote_id="salary", component="salary", unit="annum"))
    annual = annual.model_copy(update={"as_known_on": date(2026, 11, 7)})
    with pytest.raises(ValueError, match="unit"):
        price_selected_hours(annual, selection(), exposure(), ())
    rates = prices(quote(quote_id="development", component="development"))
    duplicate = allowance().model_copy(update={"quantity_id": "selected-hours"})
    with pytest.raises(ValueError, match="Duplicate quantity"):
        price_selected_hours(rates, selection(), exposure(), (duplicate,))


def test_raw_fraction_revalidation_rejects_unchecked_float_copies() -> None:
    """Serialization must not make an invalid Python float into an accepted value."""
    copied = exposure().model_copy(update={"week_quantity": 0.5})
    with pytest.raises(ValueError, match=r"instance|Decimal"):
        price_selected_hours(prices(), selection(), copied, ())
    rates = prices(quote(quote_id="development", component="development"))
    bad = allowance().model_copy(update={"quantity": 0.5})
    with pytest.raises(ValueError, match=r"instance|Decimal"):
        price_selected_hours(rates, selection(), exposure(), (bad,))


def test_snapshot_date_and_zero_exposure_keep_independent_allowance_quantity() -> None:
    """A fixed allowance is supplied separately, even when selected hours are zero."""
    rates = prices(quote(quote_id="development", component="development"))
    result = price_selected_hours(
        rates,
        selection(),
        exposure(week_quantity=Fraction(0)),
        (allowance(),),
    )
    assert_that(result.pricing.rows[0].cost == 0)
    assert_that(result.pricing.total == Fraction(10001, 200))
    later = price_selected_hours(
        prices(),
        selection(),
        exposure(valued_on=date(2026, 12, 1)),
        (),
    )
    assert_that(later.pricing.rows[0].quantity.valued_on == date(2026, 12, 1))
    with pytest.raises(ValueError, match="date"):
        price_selected_hours(
            prices(),
            selection(),
            exposure(week_quantity=Fraction(0), valued_on=date(2027, 1, 1)),
            (),
        )


def test_request_json_and_decimal_exposure_compatibility() -> None:
    """Public JSON keeps exact fractions and existing Decimal inputs still work."""
    data = exposure(week_quantity=Fraction(2, 3))
    restored = HoursPricingRequest.model_validate_json(data.model_dump_json())
    assert_that(restored.week_quantity == Fraction(2, 3))
    result = price_selected_hours(prices(), selection(), restored, ())
    assert_that(result.pricing.total == Fraction(42000, 73))
    decimal = price_selected_hours(
        prices(),
        selection(),
        exposure(week_quantity=Decimal("0.5")),
        (),
    )
    assert_that(decimal.pricing.total == Fraction(31500, 73))


def test_mutually_exclusive_allowances_are_rejected_even_at_zero() -> None:
    """Alternative condition categories must not become additive ledger rows."""
    rates = prices(
        quote(quote_id="development", component="development"),
        quote(quote_id="training", component="training"),
    )
    alternative = quantity(
        quantity_id="training",
        quote_id="training",
        unit="fortnight",
        quantity=Fraction(0),
        valued_on=date(2026, 11, 7),
    )
    data = exposure(exclusive_component_groups=(("development", "training"),))
    with pytest.raises(ValueError, match="Mutually exclusive"):
        price_selected_hours(rates, selection(), data, (allowance(), alternative))
    valid = price_selected_hours(rates, selection(), data, (allowance(),))
    assert_that(valid.pricing.total == Fraction(63000, 73) + Fraction(10001, 200))


def test_base_included_alternative_participates_in_exclusion_check() -> None:
    """A loaded base cannot hide one member of an exclusive condition group."""
    rates = prices(quote(quote_id="development", component="development"))
    data = exposure(
        base_included_components=("training",),
        exclusive_component_groups=(("development", "training"),),
    )
    with pytest.raises(ValueError, match="Mutually exclusive"):
        price_selected_hours(rates, selection(), data, (allowance(),))


@pytest.mark.parametrize("groups", [(("a",),), (("a", "a"),), (("a", "b"), ("b", "a"))])
def test_malformed_exclusive_groups_fail(groups: tuple[tuple[str, ...], ...]) -> None:
    """Group declarations retain distinct alternatives without duplicate sets."""
    with pytest.raises(ValueError, match="Exclusive component"):
        exposure(exclusive_component_groups=groups)


def test_dated_price_exposures_preserve_quantity_at_a_rate_change() -> None:
    """Explicit exposure partitions use separate prices without rounding hours."""
    rates = release(
        quote(
            quote_id="salary",
            component="salary",
            unit="hour",
            amount=Decimal(30),
            ends_on=date(2026, 12, 1),
        ),
        quote(
            quote_id="salary-2",
            component="salary",
            unit="hour",
            amount=Decimal(35),
            starts_on=date(2026, 12, 1),
        ),
    ).model_copy(update={"as_known_on": date(2026, 11, 7)})
    first = price_selected_hours(
        rates,
        selection(),
        exposure(week_quantity=Fraction(1, 2)),
        (),
    )
    second = price_selected_hours(
        rates,
        selection(),
        exposure(
            quantity_id="later-hours",
            quote_id="salary-2",
            week_quantity=Fraction(1, 2),
            valued_on=date(2026, 12, 1),
        ),
        (),
    )
    assert_that(first.pricing.total + second.pricing.total == Fraction(68250, 73))
    assert_that(
        Fraction(first.pricing.rows[0].quantity.quantity)
        + Fraction(second.pricing.rows[0].quantity.quantity)
        == Fraction(2100, 73),
    )
