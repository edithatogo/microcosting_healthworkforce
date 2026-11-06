# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Ceiling grouped physical exposure without inventing worked or paid intervals."""

from datetime import UTC, date, datetime, timedelta
from fractions import Fraction
from zoneinfo import ZoneInfo

import pytest

from src.started_units import (
    ExposureInterval,
    StartedUnitRule,
    StartedUnitWindow,
    price_started_units,
)
from tests.checks import assert_that
from tests.test_crib_away import release
from tests.test_exclusive_quotes import rule as exclusive_rule

HOUR_MICROS = 3600000000
DST_ELAPSED_HOURS = 23


def policy(**changes: object) -> StartedUnitRule:
    """Use an explicitly reviewed fictional started-occasion quantum."""
    values: dict[str, object] = dict(exclusive_rule())
    values.pop("components")
    values.update(
        {
            "component": "single_context",
            "quantum": timedelta(hours=1),
            "method": "ceil_grouped_elapsed_units_v1",
            "grouping_basis": "Synthetic one complete reviewed group",
        },
    )
    values.update(changes)
    return StartedUnitRule.model_validate(values)


def interval(minutes: int = 60, **changes: object) -> ExposureInterval:
    """Supply physical exposure with exact microsecond boundaries."""
    start = datetime(2026, 7, 10, 7, tzinfo=UTC)
    values: dict[str, object] = {
        "interval_id": "i1",
        "starts_at": start,
        "ends_at": start + timedelta(minutes=minutes),
    }
    values.update(changes)
    return ExposureInterval.model_validate(values)


def window(**changes: object) -> StartedUnitWindow:
    """Keep a complete source-qualified group distinct from its exposure pieces."""
    start = datetime(2026, 7, 10, 6, tzinfo=UTC)
    values: dict[str, object] = {
        "window_id": "w1",
        "resource_id": "worker-a",
        "starts_at": start,
        "ends_at": start + timedelta(hours=5),
        "valued_on": date(2026, 7, 10),
        "quote_id": "single_context-2026",
        "intervals": (interval(),),
        "no_exposure_confirmed": False,
        "eligibility_verified": True,
        "history_complete": True,
        "input_kind": "observed_case_evidence",
        "basis": "Synthetic complete group",
        "evidence_id": "group-evidence",
        "evidence_sha256": "b" * 64,
        "known_on": date(2026, 11, 7),
    }
    values.update(changes)
    return StartedUnitWindow.model_validate(values)


@pytest.mark.parametrize(
    ("micros", "units"),
    [
        (1, 1),
        (3600000000, 1),
        (3600000001, 2),
        (7200000000, 2),
    ],
)
def test_exact_ceiling_boundaries(micros: int, units: int) -> None:
    """A microsecond over the quantum adds one unit; exact boundaries do not."""
    a = interval(ends_at=interval().starts_at + timedelta(microseconds=micros))
    result = price_started_units(policy(), release(), (window(intervals=(a,)),))
    row = result.quantities[0]
    assert_that(row.payable_units == units)
    assert_that(row.exposure_microseconds == micros)
    assert_that(row.rounding_increment_microseconds == units * 3600000000 - micros)
    assert_that(result.prices.total == Fraction(1101 * units, 100))
    assert_that(not result.scenario)


def test_group_sum_is_segmentation_invariant_and_excludes_gaps() -> None:
    """Several fragments round once together rather than once per fragment."""
    a = interval(30)
    b = interval(
        30,
        interval_id="i2",
        starts_at=a.ends_at + timedelta(minutes=10),
        ends_at=a.ends_at + timedelta(minutes=40),
    )
    fragmented = price_started_units(policy(), release(), (window(intervals=(b, a)),))
    whole = price_started_units(policy(), release(), (window(),))
    assert_that(fragmented.prices.total == whole.prices.total)
    assert_that(fragmented.quantities[0].exposure_microseconds == HOUR_MICROS)
    assert_that(fragmented.quantities[0].payable_units == 1)


def test_known_zero_stays_distinct_from_unknown() -> None:
    """Zero requires explicit negative evidence, source coverage and selected price."""
    result = price_started_units(
        policy(),
        release(),
        (
            window(
                intervals=(),
                no_exposure_confirmed=True,
            ),
        ),
    )
    assert_that(result.quantities[0].payable_units == 0)
    assert_that(result.prices.total == 0)
    assert_that(len(result.prices.rows) == 1)
    for change in [
        {"intervals": ()},
        {"no_exposure_confirmed": True},
        {"history_complete": False},
        {"eligibility_verified": False},
    ]:
        with pytest.raises(ValueError, match="complete eligible history"):
            price_started_units(
                policy(),
                release(),
                (window().model_copy(update=change),),
            )


@pytest.mark.parametrize(
    "changes",
    [
        {"interval_id": " "},
        {"ends_at": interval().starts_at},
        {"starts_at": interval().starts_at.replace(tzinfo=None)},
        {"extra": "unreviewed"},
    ],
)
def test_forged_interval_fields_revalidated(changes: dict[str, object]) -> None:
    """Nested unchecked models cannot bypass timing, identity or strict schemas."""
    a = interval().model_copy(update=changes)
    with pytest.raises(ValueError, match=r"blank|positive|timezone|Extra inputs"):
        price_started_units(
            policy(),
            release(),
            (window().model_copy(update={"intervals": (a,)}),),
        )


def test_overlap_duplicate_and_outside_intervals_fail() -> None:
    """The same physical time cannot be counted twice or outside its group."""
    a = interval()
    for intervals in [
        (a, a),
        (a, a.model_copy(update={"interval_id": "i2"})),
        (interval(ends_at=window().ends_at + timedelta(seconds=1)),),
    ]:
        with pytest.raises(ValueError, match="unique IDs, containment and no overlap"):
            price_started_units(policy(), release(), (window(intervals=intervals),))


@pytest.mark.parametrize(
    "changes",
    [
        {"quantum": timedelta(0)},
        {"quantum": timedelta(seconds=-1)},
        {"reviewed": False},
        {"method": "round_each_fragment"},
        {"grouping_basis": " "},
        {"local_timezone": "Invalid/NoSuchZone"},
        {"source_sha256": "c" * 64},
        {"component": "other"},
        {"unit": "hour"},
        {"employer": "other"},
    ],
)
def test_policy_review_scope_and_basis_cannot_be_bypassed(
    changes: dict[str, object],
) -> None:
    """Require reviewed ceiling policy and matching price context."""
    p = policy().model_copy(update=changes)
    with pytest.raises(
        ValueError,
        match=r"review|method|blank|hash|quote|scope|timezone",
    ):
        price_started_units(p, release(), (window(),))


def test_window_date_knowledge_and_unknown_inputs_fail() -> None:
    """A valuation date cannot hide uncovered groups, missing or future evidence."""
    for change in [
        {"known_on": date(2026, 11, 8)},
        {"known_on": date(2026, 7, 9)},
        {"valued_on": date(2026, 7, 11)},
        {"starts_at": datetime(2026, 7, 9, tzinfo=UTC)},
        {"quote_id": "missing"},
        {"extra": "ignored"},
    ]:
        with pytest.raises(ValueError, match=r"coverage|quote|Extra inputs"):
            price_started_units(
                policy(),
                release(),
                (window().model_copy(update=change),),
            )
    with pytest.raises(ValueError, match="nonempty uniquely identified"):
        price_started_units(policy(), release(), ())


def test_window_overlap_even_zero_and_distinct_resources() -> None:
    """Known zero does not bypass complete history or duplicate group checks."""
    a = window(intervals=(), no_exposure_confirmed=True)
    with pytest.raises(ValueError, match="overlap"):
        price_started_units(
            policy(),
            release(),
            (a, a.model_copy(update={"window_id": "w2"})),
        )
    with pytest.raises(ValueError, match="uniquely identified"):
        price_started_units(policy(), release(), (a, a))
    b = window(window_id="w2", resource_id="worker-b")
    result = price_started_units(policy(), release(), (a, b))
    assert_that(result.prices.total == Fraction(1101, 100))


def test_dated_groups_price_versions_and_keep_row_assumptions() -> None:
    """Dynamic groups select named prices while evidence kinds remain per group."""
    a = window()
    old_interval = interval(
        starts_at=interval().starts_at - timedelta(days=1),
        ends_at=interval().ends_at - timedelta(days=1),
    )
    old = window(
        window_id="old",
        starts_at=a.starts_at - timedelta(days=1),
        ends_at=a.ends_at - timedelta(days=1),
        valued_on=date(2026, 7, 9),
        intervals=(old_interval,),
        quote_id="single_context-2025",
        input_kind="analyst_assumption",
    )
    result = price_started_units(policy(), release(), (a, old))
    assert_that(result.prices.total == Fraction(1051, 50))
    assert_that(result.scenario)
    assert_that(
        [r.quantity.quantity_kind for r in result.prices.rows]
        == ["analyst_assumption", "observed_use"],
    )


def test_dst_uses_explicit_elapsed_basis_without_roster_hour_conversion() -> None:
    """Use 23 elapsed hours on a DST day without inventing roster hours."""
    zone = ZoneInfo("Australia/Sydney")
    start, end = datetime(2026, 10, 4, tzinfo=zone), datetime(2026, 10, 5, tzinfo=zone)
    a = ExposureInterval(interval_id="dst", starts_at=start, ends_at=end)
    w = window(
        starts_at=start,
        ends_at=end,
        valued_on=date(2026, 10, 4),
        intervals=(a,),
    )
    result = price_started_units(policy(), release(), (w,))
    assert_that(result.quantities[0].payable_units == DST_ELAPSED_HOURS)
    assert_that(result.quantities[0].rounding_increment_microseconds == 0)
