# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Keep KIT eligibility/counts, actual work hours and leave extension distinct."""

from datetime import date, timedelta
from fractions import Fraction

import pytest

from src.keeping_in_touch import (
    KeepingInTouchRule,
    KITContext,
    KITExtension,
    KITLeaveInterval,
    KITPeriod,
    KITWork,
    evaluate_kit,
)
from src.source_registry import SourceRegistry
from src.unit_quotes import price_units
from tests.checks import assert_that
from tests.test_normal_pay import prices
from tests.test_source_registry import source
from tests.test_unit_quotes import quantity

BIRTH = date(2026, 2, 1)
PAID_END = BIRTH + timedelta(weeks=18)
INITIAL_END = BIRTH + timedelta(weeks=52)
EXTENSION_END = INITIAL_END + timedelta(weeks=52)


def rule(**changes: object) -> KeepingInTouchRule:
    """Select synthetic reviewed timing/count conventions, not real HR advice."""
    values: dict[str, object] = {
        "rule_id": "synthetic-kit",
        "employee_wait_days": 14,
        "employer_wait_days": 42,
        "day_limit": 10,
        "count_scope": "per_period",
        "day_count_method": "unique_calendar_day",
        "interpretation_kind": "analyst_assumption",
        "interpretation_basis": "Explicit synthetic timing/count scenario",
        "source_id": "synthetic-award-1",
        "source_sha256": "a" * 64,
        "citation": "Synthetic KIT clauses",
        "reviewed": True,
        "effective_from": date(2026, 1, 1),
        "effective_to": date(2029, 1, 1),
        "as_known_on": date(2026, 11, 7),
        "jurisdiction": "QLD",
        "employer": "Synthetic employer",
        "classification": "Synthetic grade",
        "sources": SourceRegistry(records=(source(verified_through=date(2029, 1, 1)),)),
    }
    values.update(changes)
    return KeepingInTouchRule.model_validate(values)


def context(**changes: object) -> KITContext:
    """Provide complete approved windows and paid/unpaid chronology explicitly."""
    values: dict[str, object] = {
        "scenario_id": "synthetic-episode",
        "assessed_on": date(2026, 11, 7),
        "birth_or_placement_on": BIRTH,
        "history_complete": True,
        "eligibility_verified": True,
        "eligibility_basis": "Synthetic eligible scenario",
        "local_day_basis": "Explicit supplied local calendar days",
        "periods": (
            KITPeriod(
                period_id="initial",
                starts_on=BIRTH,
                ends_on=INITIAL_END,
                kind="initial",
                approval_verified=True,
                approval_basis="Synthetic approved initial leave",
            ),
            KITPeriod(
                period_id="extension",
                starts_on=INITIAL_END,
                ends_on=EXTENSION_END,
                kind="extension",
                approval_verified=True,
                approval_basis="Synthetic approved extension",
            ),
        ),
        "leave_intervals": (
            KITLeaveInterval(
                interval_id="paid",
                period_id="initial",
                starts_on=BIRTH,
                ends_on=PAID_END,
                kind="paid",
            ),
            KITLeaveInterval(
                interval_id="unpaid",
                period_id="initial",
                starts_on=PAID_END,
                ends_on=INITIAL_END,
                kind="unpaid",
            ),
            KITLeaveInterval(
                interval_id="extended",
                period_id="extension",
                starts_on=INITIAL_END,
                ends_on=EXTENSION_END,
                kind="unpaid",
            ),
        ),
    }
    values.update(changes)
    return KITContext.model_validate(values)


def work(**changes: object) -> KITWork:
    """Declare a work fragment, its request/consent and quantity provenance."""
    values: dict[str, object] = {
        "work_id": "work-1",
        "day": BIRTH + timedelta(days=14),
        "entity_id": "Synthetic employer",
        "requested_by": "employee",
        "hours": Fraction(2),
        "quantity_kind": "analyst_assumption",
        "basis": "Synthetic KIT work",
        "purpose_verified": True,
        "employee_consented": True,
        "employer_consented": True,
        "paid_work_verified": True,
        "external_qualification_verified": False,
        "external_qualification_basis": None,
    }
    values.update(changes)
    return KITWork.model_validate(values)


def extension(**changes: object) -> KITExtension:
    """One decision per counted day prevents per-fragment duplicate extensions."""
    values: dict[str, object] = {
        "day": BIRTH + timedelta(days=14),
        "period_id": "initial",
        "paid_extension_weeks": None,
        "unit": "calendar_week",
        "review_kind": "unresolved",
        "basis": "Part-day conversion unqualified",
    }
    values.update(changes)
    return KITExtension.model_validate(values)


def test_fragments_and_other_entities_count_once_but_keep_work_hours() -> None:
    """One local day can contain multiple work fragments across entities."""
    events = (
        work(),
        work(work_id="work-2", hours=Fraction(1)),
        work(
            work_id="other",
            entity_id="Other entity",
            hours=Fraction(3),
            external_qualification_verified=True,
            external_qualification_basis="Synthetic externally qualified KIT work",
        ),
    )
    result = evaluate_kit(rule(), context(), events, (extension(),))
    assert_that(len(result.days) == 1)
    assert_that(result.days[0].ordinal == 1)
    assert_that(result.total_work_hours == Fraction(6))
    assert_that(result.local_work_hours == Fraction(3))
    assert_that(result.paid_extension_weeks is None)
    assert_that(result.unpaid_extension_weeks == 0)
    cost = price_units(
        prices(),
        (quantity(quote_id="salary", unit="hour", quantity=result.local_work_hours),),
    )
    assert_that(cost.total == Fraction(90))


def test_paid_extension_is_explicit_and_does_not_scale_with_fragments() -> None:
    """A part-day extension remains a separate approved/scenario quantity."""
    decision = extension(
        paid_extension_weeks=Fraction(1, 14),
        review_kind="analyst_assumption",
        basis="Explicit half-calendar-day scenario, not inferred from work",
    )
    result = evaluate_kit(
        rule(),
        context(),
        (work(), work(work_id="second")),
        (decision,),
    )
    assert_that(result.paid_extension_weeks == Fraction(1, 14))
    assert_that(result.known_paid_extension_weeks == Fraction(1, 14))
    assert_that(result.days[0].work_hours == Fraction(4))


def test_unpaid_work_does_not_extend_paid_or_unpaid_leave() -> None:
    """The absence classification comes from the complete approved chronology."""
    day = date(2026, 7, 1)
    decision = extension(day=day, review_kind="not_applicable")
    result = evaluate_kit(rule(), context(), (work(day=day),), (decision,))
    assert_that(result.days[0].leave_kind == "unpaid")
    assert_that(result.paid_extension_weeks == result.unpaid_extension_weeks == 0)
    with pytest.raises(ValueError, match="unpaid"):
        evaluate_kit(
            rule(),
            context(),
            (work(day=day),),
            (
                extension(
                    day=day,
                    paid_extension_weeks=Fraction(1, 7),
                    review_kind="analyst_assumption",
                ),
            ),
        )


def test_request_timing_and_declared_day14_boundary() -> None:
    """Employee/employer waits and the selected endpoint are independent gates."""
    evaluate_kit(rule(), context(), (work(),), (extension(),))
    with pytest.raises(ValueError, match="timing"):
        evaluate_kit(rule(employee_wait_days=15), context(), (work(),), (extension(),))
    with pytest.raises(ValueError, match="timing"):
        evaluate_kit(
            rule(),
            context(),
            (work(requested_by="employer"),),
            (extension(),),
        )
    day = BIRTH + timedelta(days=42)
    evaluate_kit(
        rule(),
        context(),
        (work(day=day, requested_by="employer"),),
        (extension(day=day),),
    )


def test_initial_and_extension_limits_follow_explicit_count_scope() -> None:
    """The conservative whole-episode scenario remains distinct from per-period."""
    events = tuple(
        work(work_id=f"work-{i}", day=BIRTH + timedelta(days=14 + i)) for i in range(10)
    )
    decisions = tuple(extension(day=e.day) for e in events)
    extra = work(work_id="extended", day=INITIAL_END)
    ext_decision = extension(
        day=INITIAL_END,
        period_id="extension",
        review_kind="not_applicable",
    )
    per_period = evaluate_kit(
        rule(),
        context(),
        (*events, extra),
        (*decisions, ext_decision),
    )
    assert_that(per_period.days[-1].ordinal == 1)
    with pytest.raises(ValueError, match="limit"):
        evaluate_kit(
            rule(count_scope="whole_episode"),
            context(),
            (*events, extra),
            (*decisions, ext_decision),
        )
    overflow = work(work_id="overflow", day=BIRTH + timedelta(days=24))
    with pytest.raises(ValueError, match="limit"):
        evaluate_kit(
            rule(),
            context(),
            (*events, overflow),
            (*decisions, extension(day=overflow.day)),
        )


def test_complete_history_and_consent_purpose_are_required() -> None:
    """A sample or unilateral request cannot establish eligible remaining days."""
    with pytest.raises(ValueError, match="history"):
        context(history_complete=False)
    for field in [
        "employee_consented",
        "employer_consented",
        "purpose_verified",
        "paid_work_verified",
    ]:
        with pytest.raises(ValueError, match=r"consent|purpose|paid"):
            work(**{field: False})


def test_unique_work_and_one_extension_decision_per_day() -> None:
    """Unknown/missing or duplicate decisions cannot be silently counted."""
    with pytest.raises(ValueError, match="Duplicate work"):
        evaluate_kit(rule(), context(), (work(), work()), (extension(),))
    with pytest.raises(ValueError, match="decision"):
        evaluate_kit(rule(), context(), (work(),), ())
    with pytest.raises(ValueError, match="decision"):
        evaluate_kit(rule(), context(), (work(),), (extension(), extension()))
    with pytest.raises(ValueError, match="decision"):
        evaluate_kit(rule(), context(), (), (extension(),))


def test_context_requires_complete_contiguous_unpaid_extension() -> None:
    """Period/leave gaps and a paid extension contradict the selected profile."""
    current = context()
    bad_period = current.periods[1].model_copy(
        update={"starts_on": INITIAL_END + timedelta(days=1)},
    )
    with pytest.raises(ValueError, match="contiguous"):
        context(periods=(current.periods[0], bad_period))
    bad_interval = current.leave_intervals[1].model_copy(
        update={"starts_on": PAID_END + timedelta(days=1)},
    )
    with pytest.raises(ValueError, match="cover"):
        context(
            leave_intervals=(
                current.leave_intervals[0],
                bad_interval,
                current.leave_intervals[2],
            ),
        )
    paid_extension = current.leave_intervals[2].model_copy(update={"kind": "paid"})
    with pytest.raises(ValueError, match="unpaid"):
        context(leave_intervals=(*current.leave_intervals[:2], paid_extension))


def test_order_json_revalidation_and_future_observations() -> None:
    """Rational input and original day history survive order/JSON boundaries."""
    decision = extension(
        paid_extension_weeks=Fraction(1, 14),
        review_kind="analyst_assumption",
    )
    restored = KITExtension.model_validate_json(decision.model_dump_json())
    event = KITWork.model_validate_json(work().model_dump_json())
    result = evaluate_kit(rule(), context(), (event,), (restored,))
    assert_that(result.paid_extension_weeks == Fraction(1, 14))
    bad = work().model_copy(update={"hours": 0.5})
    with pytest.raises(ValueError, match=r"instance|Decimal"):
        evaluate_kit(rule(), context(), (bad,), (extension(),))
    with pytest.raises(ValueError, match="knowledge"):
        evaluate_kit(
            rule(),
            context(),
            (work(day=INITIAL_END, quantity_kind="observed_use"),),
            (
                extension(
                    day=INITIAL_END,
                    period_id="extension",
                    review_kind="not_applicable",
                ),
            ),
        )


def test_source_and_interpretation_admission() -> None:
    """A scope/hash mismatch cannot be hidden by an empty history."""
    for changes, message in [
        ({"source_sha256": "b" * 64}, "hash"),
        ({"employer": "Other"}, "scope"),
        ({"reviewed": False}, "review"),
    ]:
        with pytest.raises(ValueError, match=message):
            evaluate_kit(rule().model_copy(update=changes), context(), (), ())
    result = evaluate_kit(rule(), context(), (), ())
    assert_that(result.total_work_hours == result.paid_extension_weeks == 0)


def test_foreign_only_day_uses_capacity_without_primary_work_or_extension() -> None:
    """Qualified external history is counted but not priced as primary work."""
    event = work(
        entity_id="Other entity",
        requested_by="employer",
        external_qualification_verified=True,
        external_qualification_basis="Synthetic separately qualified external KIT day",
    )
    result = evaluate_kit(
        rule(),
        context(),
        (event,),
        (extension(review_kind="not_applicable"),),
    )
    assert_that(result.days[0].ordinal == 1)
    assert_that(result.total_work_hours == Fraction(2))
    assert_that(result.local_work_hours == result.paid_extension_weeks == 0)
    with pytest.raises(ValueError, match="external qualification"):
        evaluate_kit(
            rule(),
            context(),
            (work(entity_id="Other entity"),),
            (extension(review_kind="not_applicable"),),
        )


def test_future_approved_window_does_not_require_future_source_coverage() -> None:
    """Current-day counting is admitted at assessment/work dates, not future ends."""
    current_source = source(verified_through=date(2026, 11, 8))
    current_rule = rule(sources=SourceRegistry(records=(current_source,)))
    result = evaluate_kit(current_rule, context(), (work(),), (extension(),))
    assert_that(len(result.days) == 1)
    future = work(work_id="projected", day=INITIAL_END)
    with pytest.raises(ValueError, match="scope"):
        evaluate_kit(
            current_rule,
            context(),
            (future,),
            (
                extension(
                    day=INITIAL_END,
                    period_id="extension",
                    review_kind="not_applicable",
                ),
            ),
        )


def test_work_order_preserves_day_states_and_exact_totals() -> None:
    """Counting order is chronological and fragments do not create extra days."""
    second = work(work_id="later", day=BIRTH + timedelta(days=16), hours=Fraction(1, 3))
    events = (work(), second)
    decisions = (extension(), extension(day=second.day))
    forward = evaluate_kit(rule(), context(), events, decisions)
    reverse = evaluate_kit(
        rule(),
        context(),
        tuple(reversed(events)),
        tuple(reversed(decisions)),
    )
    assert_that(forward.days == reverse.days)
    assert_that(forward.total_work_hours == Fraction(7, 3))


@pytest.mark.parametrize(
    "changes",
    [
        {"hours": Fraction(0)},
        {"hours": Fraction(-1)},
        {"external_qualification_verified": True},
    ],
)
def test_invalid_work_quantity_or_external_declaration(
    changes: dict[str, object],
) -> None:
    """No-work or unqualified external declarations cannot consume a KIT day."""
    with pytest.raises(ValueError, match=r"greater|External"):
        work(**changes)


def test_paid_extension_review_and_unknown_known_subtotals() -> None:
    """Unknown extension days remain null alongside independently known deltas."""
    later = work(work_id="later", day=BIRTH + timedelta(days=16))
    result = evaluate_kit(
        rule(),
        context(),
        (work(), later),
        (
            extension(),
            extension(
                day=later.day,
                paid_extension_weeks=Fraction(1, 14),
                review_kind="analyst_assumption",
            ),
        ),
    )
    assert_that(result.paid_extension_weeks is None)
    assert_that(result.known_paid_extension_weeks == Fraction(1, 14))
    with pytest.raises(ValueError, match="extension"):
        extension(paid_extension_weeks=Fraction(1, 14))
    with pytest.raises(ValueError, match="extension"):
        evaluate_kit(
            rule(),
            context(),
            (work(),),
            (extension(review_kind="not_applicable"),),
        )


def test_source_date_and_knowledge_boundaries_and_outside_work() -> None:
    """Assessment/work admission applies even without a count-changing event."""
    with pytest.raises(ValueError, match="date"):
        evaluate_kit(rule(effective_to=date(2026, 11, 7)), context(), (), ())
    with pytest.raises(ValueError, match="knowledge"):
        evaluate_kit(rule(as_known_on=date(2025, 12, 31)), context(), (), ())
    with pytest.raises(ValueError, match="chronology"):
        evaluate_kit(
            rule(),
            context(),
            (work(day=EXTENSION_END),),
            (
                extension(
                    day=EXTENSION_END,
                    period_id="extension",
                    review_kind="not_applicable",
                ),
            ),
        )


def test_orphan_duplicate_interval_and_missing_approval_fail() -> None:
    """Named intervals cannot bypass the approved chronology by changing identity."""
    current = context()
    with pytest.raises(ValueError, match="identity"):
        context(leave_intervals=(*current.leave_intervals, current.leave_intervals[0]))
    orphan = current.leave_intervals[0].model_copy(update={"period_id": "absent"})
    with pytest.raises(ValueError, match="identity"):
        context(leave_intervals=(orphan, *current.leave_intervals[1:]))
    with pytest.raises(ValueError, match="approval"):
        KITPeriod.model_validate(
            {**current.periods[0].model_dump(), "approval_verified": False},
        )
