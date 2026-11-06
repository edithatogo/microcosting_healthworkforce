# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Declared quantities are independent of elapsed-time and paid-absence duration."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, localcontext
from fractions import Fraction
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from src.costing import (
    DatedResourceUse,
    ResourceUse,
    cost_dated_quantities,
    cost_static,
)
from tests.checks import assert_that
from tests.test_costing import release

START = datetime(2026, 1, 1, 11, tzinfo=UTC)
END = START + timedelta(hours=2)


def quantity() -> DatedResourceUse:
    """Declare one resource-hour over two elapsed hours, with no hidden roster."""
    return DatedResourceUse(
        quantity_id="assumed-paid-hours",
        resource_id="staff",
        starts_at=START,
        ends_at=END,
        hours=Decimal(1),
        unit="resource_hours",
        distribution="uniform_elapsed_v1",
        quantity_kind="analyst_assumption",
        quantity_basis="Synthetic declared paid quantity; no actual roster inferred",
        allocation_id="worker",
    )


def test_declared_quantity_is_not_elapsed_hours() -> None:
    """Half an hour at50 and half at70 costs60, not two elapsed hours costing120."""
    result = cost_dated_quantities(release(), (quantity(),))
    assert_that(result.ledger.total == Decimal(60))
    assert_that([r.hours for r in result.ledger.rows] == [Decimal("0.5")] * 2)
    assert_that(result.quantity_method_id == "uniform_elapsed_quantity_v1")
    assert_that(result.quantities == (quantity(),))
    assert_that(
        result.ledger.components == {"salary": Decimal(50), "on_cost": Decimal(10)},
    )


def test_constant_price_reduces_to_static_quantity_cost() -> None:
    """At a constant50/hour,1.25 declared hours cost62.5 in either interface."""
    original = release()
    constant = original.model_copy(
        update={"rates": (original.rates[0].model_copy(update={"ends_at": None}),)},
    )
    q = quantity().model_copy(update={"hours": Decimal("1.25")})
    dated = cost_dated_quantities(constant, (q,))
    static = cost_static(
        constant,
        START,
        (ResourceUse(resource_id="staff", hours=Decimal("1.25")),),
    )
    assert_that(dated.ledger.total == static.total == Decimal("62.5"))


def test_same_uniform_density_preserves_split_and_order_invariance() -> None:
    """A37minute split with.37 and.83 hours preserves the1.2hour scenario."""
    q = quantity().model_copy(update={"hours": Decimal("1.2")})
    boundary = START + timedelta(minutes=37)
    pieces = (
        q.model_copy(
            update={
                "quantity_id": "last",
                "starts_at": boundary,
                "hours": Decimal("0.83"),
            },
        ),
        q.model_copy(
            update={
                "quantity_id": "first",
                "ends_at": boundary,
                "hours": Decimal("0.37"),
            },
        ),
    )
    whole = cost_dated_quantities(release(), (q,))
    split = cost_dated_quantities(release(), pieces)
    assert_that(whole.ledger.total == split.ledger.total == Decimal(72))
    assert_that(whole.ledger.components == split.ledger.components)
    assert_that([x.quantity_id for x in split.quantities] == ["first", "last"])


def test_microsecond_boundary_keeps_exact_nonterminating_quantity() -> None:
    """Quantity fractions survive an asymmetric duration under Decimal precision6."""
    q = quantity().model_copy(update={"ends_at": END + timedelta(microseconds=1)})
    expected = Fraction(3600000000 * 50 + 3600000001 * 70, 7200000001)
    with localcontext() as context:
        context.prec = 6
        result = cost_dated_quantities(release(), (q,)).ledger
    assert_that(
        Fraction(result.exact_total_numerator, result.exact_total_denominator)
        == expected,
    )
    assert_that(
        sum(
            (
                Fraction(r.exact_hours_numerator, r.exact_hours_denominator)
                for r in result.rows
            ),
            Fraction(0),
        )
        == 1,
    )


def test_dst_does_not_invent_additional_quantity() -> None:
    """A three-elapsed-hour fallback interval still has the declared1.5hours."""
    zone = ZoneInfo("America/New_York")
    q = quantity().model_copy(
        update={
            "starts_at": datetime(2026, 11, 1, 0, 30, tzinfo=zone),
            "ends_at": datetime(2026, 11, 1, 2, 30, tzinfo=zone),
            "hours": Decimal("1.5"),
        },
    )
    result = cost_dated_quantities(release(), (q,)).ledger
    assert_that(result.total == Decimal(105))
    assert_that(result.rows[0].hours == Decimal("1.5"))
    assert_that(result.rows[0].starts_at.tzinfo == UTC)


def test_zero_and_empty_quantities_do_not_infer_missing_coverage() -> None:
    """Explicit zero validates source/rate coverage; an empty request is empty."""
    zero = quantity().model_copy(update={"hours": Decimal(0)})
    assert_that(cost_dated_quantities(release(), (zero,)).ledger.total == Decimal(0))
    assert_that(cost_dated_quantities(release(), ()).ledger.rows == ())
    gap = release().model_copy(update={"rates": (release().rates[0],)})
    with pytest.raises(ValueError, match="coverage"):
        cost_dated_quantities(gap, (zero,))


def test_source_horizon_is_checked_at_interval_end() -> None:
    """Zero quantity does not authorize a later day outside source verification."""
    original = release()
    source = original.sources.records[0].model_copy(
        update={"verified_through": date(2026, 1, 2)},
    )
    scoped = original.model_copy(
        update={"sources": original.sources.model_copy(update={"records": (source,)})},
    )
    q = quantity().model_copy(
        update={
            "starts_at": datetime(2026, 1, 1, 23, tzinfo=UTC),
            "ends_at": datetime(2026, 1, 2, 1, tzinfo=UTC),
            "hours": Decimal(0),
        },
    )
    with pytest.raises(ValueError, match="coverage"):
        cost_dated_quantities(scoped, (q,))


@pytest.mark.parametrize(
    "update",
    [
        {"hours": Decimal(-1)},
        {"starts_at": START.replace(tzinfo=None)},
        {"ends_at": START},
        {"quantity_id": " "},
        {"unit": "weeks"},
        {"distribution": "calendar_days"},
        {"allocation_id": " "},
        {"hours": Decimal(3)},
        {"quantity_kind": "entitlement"},
        {"quantity_basis": " "},
    ],
)
def test_invalid_quantity_conventions_are_revalidated(
    update: dict[str, object],
) -> None:
    """No guessed units, unsupported allocation or excess individual hours."""
    with pytest.raises(ValidationError):
        cost_dated_quantities(release(), (quantity().model_copy(update=update),))


def test_duplicate_or_overlapping_worker_quantities_fail() -> None:
    """Two separately named quantities cannot double-book the same allocation."""
    for duplicate in (
        quantity(),
        quantity().model_copy(update={"quantity_id": "other"}),
    ):
        with pytest.raises(ValueError, match=r"Duplicate|overlap"):
            cost_dated_quantities(release(), (quantity(), duplicate))


def test_unreviewed_release_capabilities_and_hashes_are_not_bypassed() -> None:
    """The new quantity interface retains all existing release admission gates."""
    original = release()
    for bad in (
        original.model_copy(update={"required_capabilities": ("leave_accrual",)}),
        original.model_copy(
            update={
                "rates": (
                    original.rates[0].model_copy(update={"source_sha256": "b" * 64}),
                ),
            },
        ),
    ):
        with pytest.raises(ValueError, match=r"Unsupported|hash"):
            cost_dated_quantities(bad, (quantity(),))


def test_aggregate_quantities_require_explicit_allocation_scope() -> None:
    """An unallocated category may represent three resource-hours over two hours."""
    q = quantity().model_copy(update={"allocation_id": None, "hours": Decimal(3)})
    assert_that(cost_dated_quantities(release(), (q,)).ledger.total == Decimal(180))


def test_explicit_units_distribution_and_quantity_basis_are_required() -> None:
    """An observed quantity still needs an explicit distribution and evidence basis."""
    for field in ("unit", "distribution", "quantity_kind", "quantity_basis"):
        data = quantity().model_dump()
        del data[field]
        with pytest.raises(ValidationError, match=field):
            DatedResourceUse.model_validate(data)
