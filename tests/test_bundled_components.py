# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Reject explicit salary inclusions that would otherwise be counted twice."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from src.condition_history import release_sha256
from src.conditions import (
    ConditionRelease,
    cost_condition_activity,
    cost_condition_snapshot,
)
from src.costing import Activity
from src.derived_components import cost_derived_snapshot
from tests.checks import assert_that
from tests.test_conditions import condition
from tests.test_derived_components import baseline, rule
from tests.test_retrospective_conditions import retrospective_release


def bundled_release() -> ConditionRelease:
    """Assert one synthetic salary already includes a development component."""
    old = baseline()
    components = tuple(
        item.model_copy(update={"included_components": ("development",)})
        if item.kind == "salary"
        else item
        for item in old.conditions
    )
    return ConditionRelease.model_validate(
        {**old.model_dump(), "conditions": components},
    )


def test_included_allowance_is_not_added_as_a_second_condition() -> None:
    """A reviewed inclusion and overlapping separate allowance fail closed."""
    base = bundled_release()
    allowance = condition("development", "fixed_annual", "1000", "AUD/year")
    with pytest.raises(ValueError, match="duplicates a salary inclusion"):
        ConditionRelease.model_validate(
            {**base.model_dump(), "conditions": (*base.conditions, allowance)},
        )
    result = cost_condition_snapshot(base, date(2026, 6, 2), Decimal(1))
    assert_that(result.total == Decimal(55))


def test_included_allowance_cannot_be_derived_again() -> None:
    """Derived additions cannot duplicate an active included component."""
    with pytest.raises(ValueError, match="duplicates a salary inclusion"):
        cost_derived_snapshot(
            bundled_release(),
            date(2026, 6, 2),
            Decimal(1),
            (rule("duplicate", "development", ("salary",), "0.05"),),
        )


def test_inclusions_preserve_existing_pins_and_change_new_hashes() -> None:
    """Old release pins remain stable and explicit inclusions affect new hashes."""
    previous = "eee025a6791fa54e8618649ac49422f23dce7ed183d6ff970918c87485136649"
    assert_that(release_sha256(retrospective_release()) == previous)
    assert_that(release_sha256(baseline()) != release_sha256(bundled_release()))


def test_invalid_inclusion_declarations_fail_closed() -> None:
    """Only salary can declare unique nonempty included components."""
    salary = condition("salary", "salary", "100000", "AUD/year")
    for invalid in (("",), ("salary",), ("x", "x")):
        with pytest.raises(ValueError, match="salary inclusions"):
            type(salary).model_validate(
                {**salary.model_dump(), "included_components": invalid},
            )
    allowance = condition("allowance", "fixed_annual", "100", "AUD/year")
    with pytest.raises(ValueError, match="salary inclusions"):
        type(allowance).model_validate(
            {**allowance.model_dump(), "included_components": ("x",)},
        )


def test_dynamic_path_revalidates_bypassed_release() -> None:
    """Forged copies cannot bypass the overlap guard during activity costing."""
    base = bundled_release()
    allowance = condition("development", "fixed_annual", "1000", "AUD/year")
    forged = base.model_copy(update={"conditions": (*base.conditions, allowance)})
    start = datetime(2026, 6, 2, 9, tzinfo=UTC)
    activity = Activity(
        activity_id="synthetic",
        resource_id="worker",
        starts_at=start,
        ends_at=start + timedelta(hours=1),
        resources=Decimal(1),
    )
    with pytest.raises(ValueError, match="duplicates a salary inclusion"):
        cost_condition_activity(forged, activity, "UTC")


def test_non_overlapping_edition_is_not_rejected() -> None:
    """A separate allowance before the bundled salary starts is distinct."""
    base = bundled_release()
    later = tuple(
        item.model_copy(update={"effective_from": date(2026, 7, 1)})
        if item.kind == "salary"
        else item
        for item in base.conditions
    )
    allowance = condition("development", "fixed_annual", "1000", "AUD/year").model_copy(
        update={"effective_to": date(2026, 7, 1)},
    )
    candidate = ConditionRelease.model_validate(
        {**base.model_dump(), "conditions": (*later, allowance)},
    )
    assert_that(candidate.conditions[-1].effective_to == date(2026, 7, 1))
