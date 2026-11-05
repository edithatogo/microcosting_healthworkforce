# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Independent arithmetic and boundary checks for static/dynamic costing."""

from datetime import UTC, datetime
from decimal import Decimal

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
