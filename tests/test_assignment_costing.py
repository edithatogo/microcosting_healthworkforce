# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Independent arithmetic for explicit assignment changes and decision knowledge."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, localcontext
from fractions import Fraction

import pytest

from src.assignment_costing import (
    AssignmentState,
    AssignmentTimeline,
    cost_assignment_activities,
    cost_assignment_snapshot,
)
from src.condition_history import ConditionHistory, ReleaseEdition
from src.conditions import ConditionRelease
from src.costing import Activity
from src.source_registry import SourceRegistry
from tests.checks import assert_that
from tests.test_conditions import condition
from tests.test_source_registry import source

START = datetime(2026, 6, 1, tzinfo=UTC)
CHANGE = START + timedelta(hours=12)
END = START + timedelta(days=1)


def release(label: str, salary: str) -> ConditionRelease:
    """Two fictional classes in one source, with explicit annual paid hours."""
    return ConditionRelease(
        release_id=label,
        jurisdiction="QLD",
        employer="Synthetic employer",
        classification=label,
        sources=SourceRegistry(
            records=(source(classifications=("step-one", "step-two")),),
        ),
        conditions=(
            condition("salary", "salary", salary, "AUD/year"),
            condition("hours", "paid_hours", "2000", "hours/year"),
        ),
    )


def timeline() -> AssignmentTimeline:
    """Explicit $50 then $60 hourly class assignments, with known decisions."""
    return AssignmentTimeline(
        timeline_id="synthetic-path-1",
        subject_id="opaque-worker",
        as_known_on=date(2026, 6, 2),
        history_complete=True,
        states=(
            AssignmentState(
                state_id="first",
                starts_at=START,
                ends_at=CHANGE,
                release=release("step-one", "100000"),
                timezone="UTC",
                decision_id="fictional-decision-one",
                decision_made_on=date(2026, 1, 1),
                decision_known_on=date(2026, 1, 1),
                earlier_effect_reviewed=False,
                decision_kind="analyst_scenario",
                decision_basis="Explicit synthetic first appointment",
                decision_reviewed=True,
            ),
            AssignmentState(
                state_id="second",
                starts_at=CHANGE,
                ends_at=END,
                release=release("step-two", "120000"),
                timezone="UTC",
                decision_id="fictional-decision-two",
                decision_made_on=date(2026, 1, 1),
                decision_known_on=date(2026, 1, 1),
                earlier_effect_reviewed=False,
                decision_kind="analyst_scenario",
                decision_basis="Explicit synthetic approved change",
                decision_reviewed=True,
            ),
        ),
    )


def activity() -> Activity:
    """One nominal resource-hour on each side of the declared change."""
    return Activity(
        activity_id="shift",
        resource_id="opaque-worker",
        starts_at=CHANGE - timedelta(hours=1),
        ends_at=CHANGE + timedelta(hours=1),
        resources=Decimal(1),
    )


def test_assignment_change_prices_each_class_with_its_own_lineage() -> None:
    """50+60=110, rather than extending either class over the whole activity."""
    result = cost_assignment_activities(timeline(), (activity(),))
    assert_that(result.total == Fraction(110))
    assert_that(result.components == {"salary": Fraction(110)})
    assert_that([r.state_id for r in result.rows] == ["first", "second"])
    assert_that([r.exact_hours for r in result.rows] == [Fraction(1), Fraction(1)])
    assert_that(
        [r.decision_id for r in result.rows]
        == [
            "fictional-decision-one",
            "fictional-decision-two",
        ],
    )
    assert_that(all(r.release_sha256 for r in result.rows))


def test_snapshot_uses_the_same_exclusive_state_boundary() -> None:
    """Two nominal hours cost100 before the change and120 at its start."""
    before = cost_assignment_snapshot(
        timeline(),
        CHANGE - timedelta(microseconds=1),
        Decimal(2),
    )
    after = cost_assignment_snapshot(timeline(), CHANGE, Decimal(2))
    assert_that(before.total == Fraction(100) and after.total == Fraction(120))
    assert_that(before.rows[0].state_id == "first")
    assert_that(after.rows[0].state_id == "second")
    with pytest.raises(ValueError, match="coverage"):
        cost_assignment_snapshot(timeline(), END, Decimal(0))


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"starts_at": CHANGE + timedelta(microseconds=1)}, "contiguous"),
        ({"starts_at": CHANGE - timedelta(microseconds=1)}, "contiguous"),
        ({"state_id": "first"}, "Duplicate"),
        ({"decision_reviewed": False}, "True"),
        ({"decision_basis": " "}, "blank"),
        ({"decision_known_on": date(2026, 8, 1)}, "not known"),
        ({"decision_made_on": date(2026, 8, 1)}, "knowledge cannot predate"),
        ({"timezone": "Unknown/Place"}, "valid IANA"),
    ],
)
def test_assignment_revalidates_copied_states(
    changes: dict[str, object],
    message: str,
) -> None:
    """A forged nested copy cannot bypass coverage, decision or clock admission."""
    current = timeline()
    second = current.states[1].model_copy(update=changes)
    changed = current.model_copy(update={"states": (current.states[0], second)})
    with pytest.raises(ValueError, match=message):
        cost_assignment_activities(changed, (activity(),))


def test_empty_unknown_duplicate_and_overlapping_activity_inputs_fail() -> None:
    """One explicit subject cannot charge duplicated or simultaneous allocations."""
    current = timeline()
    for events in (
        (),
        (activity(), activity()),
        (activity().model_copy(update={"resource_id": "another-worker"}),),
        (activity(), activity().model_copy(update={"activity_id": "parallel"})),
    ):
        with pytest.raises(ValueError, match=r"unique|subject|overlap"):
            cost_assignment_activities(current, events)
    with pytest.raises(ValueError, match="explicitly complete"):
        cost_assignment_activities(
            current.model_copy(update={"history_complete": False}),
            (activity(),),
        )


def test_exact_aggregation_and_constant_snapshot_agreement() -> None:
    """Three20minute pieces retain50 exactly even with low Decimal precision."""
    start = START + timedelta(hours=2)
    whole = activity().model_copy(
        update={
            "starts_at": start,
            "ends_at": start + timedelta(hours=1),
        },
    )
    pieces = tuple(
        whole.model_copy(
            update={
                "activity_id": f"piece-{i}",
                "starts_at": start + timedelta(minutes=20 * i),
                "ends_at": start + timedelta(minutes=20 * (i + 1)),
            },
        )
        for i in range(3)
    )
    with localcontext() as context:
        context.prec = 3
        split = cost_assignment_activities(timeline(), pieces)
        unsplit = cost_assignment_activities(timeline(), (whole,))
        static = cost_assignment_snapshot(timeline(), start, Decimal(1))
    assert_that(split.total == unsplit.total == static.total == Fraction(50))
    assert_that(split.components == unsplit.components == static.components)


def test_later_decision_does_not_rewrite_a_frozen_earlier_timeline() -> None:
    """Earlier knowledge prices100; a reviewed later-known change prices110."""
    current = timeline()
    original = current.model_copy(
        update={
            "timeline_id": "before-decision",
            "states": (current.states[0].model_copy(update={"ends_at": END}),),
        },
    )
    later = current.model_copy(
        update={
            "timeline_id": "after-decision",
            "as_known_on": date(2026, 9, 1),
            "states": (
                current.states[0],
                current.states[1].model_copy(
                    update={
                        "decision_known_on": date(2026, 8, 1),
                    },
                ),
            ),
        },
    )
    before = cost_assignment_activities(original, (activity(),))
    after = cost_assignment_activities(later, (activity(),))
    assert_that(before.total == Fraction(100) and after.total == Fraction(110))
    assert_that(before.timeline_sha256 != after.timeline_sha256)
    assert_that(cost_assignment_activities(original, (activity(),)) == before)


@pytest.mark.parametrize("failure", ["future-source", "future-release", "reused-id"])
def test_timeline_does_not_hide_release_or_source_knowledge(failure: str) -> None:
    """A decision assertion cannot backdate a release or alias different editions."""
    current = timeline()
    second = current.states[1]
    price = second.release
    if failure == "future-source":
        record = price.sources.records[0].model_copy(
            update={
                "retrieved_at": datetime(2026, 8, 1, tzinfo=UTC),
            },
        )
        price = price.model_copy(update={"sources": SourceRegistry(records=(record,))})
    elif failure == "future-release":
        price = price.model_copy(update={"as_known_at": date(2026, 8, 1)})
    else:
        price = price.model_copy(
            update={
                "release_id": current.states[0].release.release_id,
            },
        )
    altered = current.model_copy(
        update={
            "states": (
                current.states[0],
                second.model_copy(update={"release": price}),
            ),
        },
    )
    with pytest.raises(ValueError, match=r"knowledge|not known|identity reused"):
        cost_assignment_snapshot(altered, CHANGE, Decimal(0))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("applicability", "unresolved"),
        ("sha256", "b" * 64),
        ("verified_through", date(2026, 6, 1)),
    ],
)
def test_timeline_preserves_nested_price_source_admission(
    field: str,
    value: object,
) -> None:
    """Copied price/source models are revalidated even for a zero quantity."""
    current = timeline()
    state = current.states[0]
    record = state.release.sources.records[0].model_copy(update={field: value})
    registry = state.release.sources.model_copy(update={"records": (record,)})
    changed = state.release.model_copy(update={"sources": registry})
    altered = current.model_copy(
        update={
            "states": (
                state.model_copy(update={"release": changed}),
                current.states[1],
            ),
        },
    )
    with pytest.raises(ValueError, match=r"coverage|hash"):
        cost_assignment_snapshot(altered, START, Decimal(0))


def test_one_state_still_splits_at_the_existing_wage_date_boundary() -> None:
    """One hour at50 plus one at100 costs150 without a new assignment decision."""
    current = timeline()
    base = current.states[0].release
    first = base.conditions[0].model_copy(
        update={
            "condition_id": "salary-before",
            "effective_to": date(2026, 6, 2),
        },
    )
    second = base.conditions[0].model_copy(
        update={
            "condition_id": "salary-after",
            "effective_from": date(2026, 6, 2),
            "value": Decimal(200000),
        },
    )
    price = base.model_copy(
        update={
            "conditions": (first, second, base.conditions[1]),
        },
    )
    path = current.model_copy(
        update={
            "states": (
                current.states[0].model_copy(
                    update={
                        "ends_at": END + timedelta(days=1),
                        "release": price,
                    },
                ),
            ),
        },
    )
    work = activity().model_copy(
        update={
            "starts_at": END - timedelta(hours=1),
            "ends_at": END + timedelta(hours=1),
        },
    )
    result = cost_assignment_activities(path, (work,))
    assert_that(result.total == Fraction(150))
    assert_that({r.state_id for r in result.rows} == {"first"})
    assert_that(result.rows[0].condition_ids != result.rows[1].condition_ids)


def test_dst_repeated_hour_uses_elapsed_time_and_explicit_transition() -> None:
    """Two elapsed hours across Sydney's repeated hour retain one of each price."""
    current = timeline()
    start = datetime(2026, 4, 4, 14, tzinfo=UTC)
    change = start + timedelta(hours=2)
    path = current.model_copy(
        update={
            "states": (
                current.states[0].model_copy(
                    update={
                        "starts_at": start,
                        "ends_at": change,
                        "timezone": "Australia/Sydney",
                    },
                ),
                current.states[1].model_copy(
                    update={
                        "starts_at": change,
                        "ends_at": start + timedelta(hours=4),
                        "timezone": "Australia/Sydney",
                    },
                ),
            ),
        },
    )
    work = activity().model_copy(
        update={
            "starts_at": change - timedelta(hours=1),
            "ends_at": change + timedelta(hours=1),
        },
    )
    result = cost_assignment_activities(path, (work,))
    assert_that(result.total == Fraction(110))
    assert_that(sum((r.exact_hours for r in result.rows), Fraction(0)) == Fraction(2))


def test_zero_still_requires_coverage_and_one_subject_quantity() -> None:
    """A known zero is priced, but cannot conceal an uncovered tail."""
    zero = activity().model_copy(update={"resources": Decimal(0)})
    assert_that(cost_assignment_activities(timeline(), (zero,)).total == 0)
    with pytest.raises(ValueError, match="coverage"):
        cost_assignment_activities(
            timeline(),
            (
                zero.model_copy(
                    update={
                        "ends_at": END + timedelta(microseconds=1),
                    },
                ),
            ),
        )
    with pytest.raises(ValueError, match="subject"):
        cost_assignment_activities(
            timeline(),
            (
                activity().model_copy(
                    update={
                        "resources": Decimal(2),
                    },
                ),
            ),
        )
    with pytest.raises(ValueError, match="aware"):
        cost_assignment_snapshot(timeline(), START.replace(tzinfo=None), Decimal(1))


def test_existing_release_history_keeps_its_single_classification_contract() -> None:
    """The new explicit assignment path does not relax old release lineage checks."""
    current = timeline()
    first, second = (s.release for s in current.states)
    with pytest.raises(ValueError, match="scope"):
        ConditionHistory(
            editions=(
                ReleaseEdition(release=first, known_from=date(2026, 1, 1)),
                ReleaseEdition(
                    release=second,
                    known_from=date(2026, 1, 2),
                    supersedes=first.release_id,
                ),
            ),
        )


def test_backdated_decision_needs_review_separate_from_late_discovery() -> None:
    """An August decision effective in June needs explicit earlier-effect review."""
    current = timeline()
    state = current.states[1].model_copy(
        update={
            "decision_made_on": date(2026, 8, 1),
            "decision_known_on": date(2026, 8, 1),
        },
    )
    later = current.model_copy(
        update={
            "as_known_on": date(2026, 9, 1),
            "states": (current.states[0], state),
        },
    )
    with pytest.raises(ValueError, match="Earlier assignment effect"):
        cost_assignment_activities(later, (activity(),))
    reviewed = later.model_copy(
        update={
            "states": (
                current.states[0],
                state.model_copy(update={"earlier_effect_reviewed": True}),
            ),
        },
    )
    assert_that(
        cost_assignment_activities(reviewed, (activity(),)).total == Fraction(110),
    )
