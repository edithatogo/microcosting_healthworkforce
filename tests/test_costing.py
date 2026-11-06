# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Independent arithmetic and boundary checks for static/dynamic costing."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal, localcontext
from fractions import Fraction

import pytest

from src.costing import (
    Activity,
    CostRelease,
    RatePeriod,
    ResourceUse,
    cost_dynamic,
    cost_static,
)
from src.source_registry import SourceRegistry
from tests.checks import assert_that
from tests.test_source_registry import source


def release() -> CostRelease:
    """Two synthetic reviewed hourly rates, effective on either side of noon."""
    return CostRelease(
        release_id="synthetic-1",
        method_id="flat_hourly_v1",
        currency="AUD",
        sources=SourceRegistry(records=(source(),)),
        rates=(
            RatePeriod(
                rate_id="morning",
                resource_id="staff",
                jurisdiction="QLD",
                employer="Synthetic employer",
                classification="Synthetic grade",
                starts_at=datetime(2026, 1, 1, tzinfo=UTC),
                ends_at=datetime(2026, 1, 1, 12, tzinfo=UTC),
                components={"salary": Decimal(40), "on_cost": Decimal(10)},
                source_id="synthetic-award-1",
                source_sha256="a" * 64,
                citation="Synthetic clause 1",
                reviewed=True,
            ),
            RatePeriod(
                rate_id="afternoon",
                resource_id="staff",
                jurisdiction="QLD",
                employer="Synthetic employer",
                classification="Synthetic grade",
                starts_at=datetime(2026, 1, 1, 12, tzinfo=UTC),
                components={"salary": Decimal(60), "on_cost": Decimal(10)},
                source_id="synthetic-award-1",
                source_sha256="a" * 64,
                citation="Synthetic clause 2",
                reviewed=True,
            ),
        ),
    )


def test_static_components_scale_with_explicit_resource_hours() -> None:
    """Two hours at 40+10 cost 100 with component and release lineage."""
    result = cost_static(
        release(),
        datetime(2026, 1, 1, 11, tzinfo=UTC),
        (ResourceUse(resource_id="staff", hours=Decimal(2)),),
    )
    assert_that(result.total == Decimal(100))
    assert_that(result.components == {"salary": Decimal(80), "on_cost": Decimal(20)})
    assert_that(result.release_id == "synthetic-1")


def test_dynamic_splits_at_effective_boundary_and_conserves_hours() -> None:
    """An hour on each side of noon costs 50+70, not one snapshot rate."""
    result = cost_dynamic(
        release(),
        (
            Activity(
                activity_id="work",
                resource_id="staff",
                starts_at=datetime(2026, 1, 1, 11, tzinfo=UTC),
                ends_at=datetime(2026, 1, 1, 13, tzinfo=UTC),
                resources=Decimal(1),
            ),
        ),
    )
    assert_that(result.total == Decimal(120))
    assert_that(sum((r.hours for r in result.rows), Decimal(0)) == Decimal(2))
    assert_that([r.rate_id for r in result.rows] == ["morning", "afternoon"])


def test_uncovered_time_and_unreviewed_rates_fail_closed() -> None:
    """Missing history and unsupported conditions do not become zero-cost work."""
    with pytest.raises(ValueError, match="coverage"):
        cost_static(
            release(),
            datetime(2025, 1, 1, tzinfo=UTC),
            (ResourceUse(resource_id="staff", hours=Decimal(1)),),
        )
    invalid = release().model_copy(
        update={"required_capabilities": ("cumulative_overtime",)},
    )
    with pytest.raises(ValueError, match="Unsupported"):
        cost_static(
            invalid,
            datetime(2026, 1, 1, 11, tzinfo=UTC),
            (ResourceUse(resource_id="staff", hours=Decimal(1)),),
        )


def test_static_and_dynamic_agree_for_constant_rate() -> None:
    """A one-hour activity has the same cost as its static resource hours."""
    when = datetime(2026, 1, 1, 10, tzinfo=UTC)
    static = cost_static(
        release(),
        when,
        (ResourceUse(resource_id="staff", hours=Decimal(1)),),
    )
    dynamic = cost_dynamic(
        release(),
        (
            Activity(
                activity_id="one",
                resource_id="staff",
                starts_at=when,
                ends_at=datetime(2026, 1, 1, 11, tzinfo=UTC),
                resources=Decimal(1),
            ),
        ),
    )
    assert_that(
        static.total == dynamic.total and static.components == dynamic.components,
    )


def test_dynamic_cannot_extend_beyond_source_verification() -> None:
    """An open-ended rate does not extend a source's evidence horizon."""
    with pytest.raises(ValueError, match="coverage"):
        cost_dynamic(
            release(),
            (
                Activity(
                    activity_id="later",
                    resource_id="staff",
                    starts_at=datetime(2026, 12, 31, 23, tzinfo=UTC),
                    ends_at=datetime(2027, 1, 1, 1, tzinfo=UTC),
                    resources=Decimal(1),
                ),
            ),
        )


def test_altered_rate_source_hash_is_rejected() -> None:
    """Source edition cannot be silently swapped after rate review."""
    current = release()
    altered = current.rates[0].model_copy(update={"source_sha256": "b" * 64})
    changed = current.model_copy(update={"rates": (altered, *current.rates[1:])})
    with pytest.raises(ValueError, match="hash"):
        cost_static(changed, datetime(2026, 1, 1, 11, tzinfo=UTC), ())


def test_exact_flat_activity_cost_is_invariant_to_fractional_hour_splits() -> None:
    """Flat hourly costs keep an exact rational total across three 20-minute slices."""
    start = datetime(2026, 1, 1, 9, tzinfo=UTC)
    whole = Activity(
        activity_id="whole",
        resource_id="staff",
        starts_at=start,
        ends_at=start + timedelta(hours=1),
        resources=Decimal(1),
    )
    parts = tuple(
        Activity(
            activity_id=str(i),
            resource_id="staff",
            starts_at=start + timedelta(minutes=i),
            ends_at=start + timedelta(minutes=i + 20),
            resources=Decimal(1),
        )
        for i in (0, 20, 40)
    )
    a = cost_dynamic(release(), (whole,))
    b = cost_dynamic(release(), parts)
    assert_that(
        Fraction(a.exact_total_numerator, a.exact_total_denominator) == Fraction(50),
    )
    assert_that(
        Fraction(a.exact_total_numerator, a.exact_total_denominator)
        == Fraction(b.exact_total_numerator, b.exact_total_denominator),
    )


def test_flat_cost_revalidates_copied_resource_quantities_and_activity() -> None:
    """Unvalidated model copies cannot bypass nonnegative quantity and time checks."""
    use = ResourceUse(resource_id="staff", hours=Decimal(1)).model_copy(
        update={"hours": Decimal(-1)},
    )
    with pytest.raises(ValueError, match="greater than or equal to 0"):
        cost_static(release(), datetime(2026, 1, 1, 10, tzinfo=UTC), (use,))
    activity = Activity(
        activity_id="a",
        resource_id="staff",
        starts_at=datetime(2026, 1, 1, 10, tzinfo=UTC),
        ends_at=datetime(2026, 1, 1, 11, tzinfo=UTC),
        resources=Decimal(1),
    ).model_copy(update={"resources": Decimal(-1)})
    with pytest.raises(ValueError, match="greater than or equal to 0"):
        cost_dynamic(release(), (activity,))


def test_flat_exact_static_and_dynamic_cost_agree_for_constant_rate() -> None:
    """Equivalent one-hour snapshot and activity produce identical rational costs."""
    start = datetime(2026, 1, 1, 9, tzinfo=UTC)
    snap = cost_static(
        release(),
        start,
        (ResourceUse(resource_id="staff", hours=Decimal(1)),),
    )
    activity = Activity(
        activity_id="work",
        resource_id="staff",
        starts_at=start,
        ends_at=start + timedelta(hours=1),
        resources=Decimal(1),
    )
    dynamic = cost_dynamic(release(), (activity,))
    assert_that(
        Fraction(snap.exact_total_numerator, snap.exact_total_denominator)
        == Fraction(dynamic.exact_total_numerator, dynamic.exact_total_denominator)
        == Fraction(50),
    )


def test_explicit_allocations_reject_overlaps_but_allow_parallel_workers() -> None:
    """Worker identity, not the shared rate category, determines overlap."""
    start = datetime(2026, 1, 1, 10, tzinfo=UTC)
    first = Activity(
        activity_id="first",
        resource_id="staff",
        allocation_id="opaque-1",
        starts_at=start,
        ends_at=start + timedelta(hours=1),
        resources=Decimal(1),
    )
    overlapping = first.model_copy(update={"activity_id": "second"})
    with pytest.raises(ValueError, match="overlap"):
        cost_dynamic(release(), (first, overlapping))
    # Identity is global across rate categories, even if the later rate is absent.
    cross_category = overlapping.model_copy(update={"resource_id": "other-category"})
    with pytest.raises(ValueError, match="overlap"):
        cost_dynamic(release(), (first, cross_category))
    # Without allocation identities the caller supplies aggregate quantities.
    aggregate = first.model_copy(update={"allocation_id": None})
    aggregate_two = aggregate.model_copy(update={"activity_id": "aggregate-two"})
    assert_that(
        cost_dynamic(release(), (aggregate, aggregate_two)).total == Decimal(100),
    )
    second = overlapping.model_copy(update={"allocation_id": "opaque-2"})
    result = cost_dynamic(release(), (first, second))
    assert_that(result.total == Decimal(100))
    assert_that([row.allocation_id for row in result.rows] == ["opaque-1", "opaque-2"])
    adjacent = first.model_copy(
        update={
            "activity_id": "next",
            "starts_at": first.ends_at,
            "ends_at": first.ends_at + timedelta(hours=1),
        },
    )
    assert_that(
        [r.activity_id for r in cost_dynamic(release(), (adjacent, first)).rows]
        == ["next", "first"],
    )


def test_allocation_identity_requires_one_resource_and_nonblank_id() -> None:
    """An individual allocation cannot represent several workers or a blank ID."""
    base = {
        "activity_id": "a",
        "resource_id": "staff",
        "starts_at": datetime(2026, 1, 1, 10, tzinfo=UTC),
        "ends_at": datetime(2026, 1, 1, 11, tzinfo=UTC),
        "resources": Decimal(2),
        "allocation_id": "opaque",
    }
    with pytest.raises(ValueError, match="one resource"):
        Activity.model_validate(base)
    base.update({"resources": Decimal(1), "allocation_id": " "})
    with pytest.raises(ValueError, match="blank"):
        Activity.model_validate(base)


@pytest.mark.parametrize("precision", [6, 28])
def test_exact_component_aggregation_is_independent_of_segmentation(
    precision: int,
) -> None:
    """One25-minute activity and5+20 minutes have identical projected totals."""
    start = datetime(2026, 1, 1, 10, tzinfo=UTC)
    activity = Activity(
        activity_id="whole",
        resource_id="staff",
        allocation_id="worker",
        starts_at=start,
        ends_at=start + timedelta(minutes=25),
        resources=Decimal(1),
    )
    with localcontext() as context:
        context.prec = precision
        whole = cost_dynamic(release(), (activity,))
        parts = cost_dynamic(
            release(),
            (
                activity.model_copy(
                    update={
                        "activity_id": "first",
                        "ends_at": start + timedelta(minutes=5),
                    },
                ),
                activity.model_copy(
                    update={
                        "activity_id": "second",
                        "starts_at": start + timedelta(minutes=5),
                    },
                ),
            ),
        )
        assert_that(whole.total == parts.total == Decimal(125) / Decimal(6))
        assert_that(whole.components == parts.components)
        assert_that(
            Fraction(whole.exact_total_numerator, whole.exact_total_denominator)
            == Fraction(parts.exact_total_numerator, parts.exact_total_denominator)
            == Fraction(125, 6),
        )
        assert_that(
            sum(
                (
                    Fraction(row.exact_hours_numerator, row.exact_hours_denominator)
                    for row in parts.rows
                ),
                Fraction(0),
            )
            == Fraction(5, 12),
        )
