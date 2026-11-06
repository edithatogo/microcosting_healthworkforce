# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Select a complete historical hours base with explicit averaging conventions."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, localcontext
from fractions import Fraction

import pytest

from src.historical_hours import (
    HistoricalHours,
    HoursHistoryRequest,
    NormalHoursRule,
    select_normal_hours,
)
from src.source_registry import SourceRegistry
from tests.checks import assert_that
from tests.test_source_registry import source


def rule(**changes: object) -> NormalHoursRule:
    """Make an explicitly chosen synthetic source/method, not a real entitlement."""
    values: dict[str, object] = {
        "rule_id": "synthetic-history",
        "source_id": "synthetic-award-1",
        "source_sha256": "a" * 64,
        "citation": "Synthetic comparison clause",
        "effective_from": date(2026, 1, 1),
        "effective_to": date(2027, 1, 1),
        "reviewed": True,
        "lookback_months": 12,
        "minimum_service_weeks": 40,
        "anniversary_method": "clamp_last_day_v1",
        "jurisdiction": "QLD",
        "employer": "Synthetic employer",
        "classification": "Synthetic grade",
        "as_known_on": date(2026, 11, 7),
        "sources": SourceRegistry(records=(source(),)),
    }
    values.update(changes)
    return NormalHoursRule.model_validate(values)


def request(**changes: object) -> HoursHistoryRequest:
    """Supply the averaging exposure; never derive it from a year constant."""
    values: dict[str, object] = {
        "leave_starts_on": date(2026, 11, 7),
        "continuous_service_from": date(2024, 1, 1),
        "continuous_service_verified": True,
        "history_complete": True,
        "current_hours_per_week": Decimal(20),
        "equivalent_weeks_numerator": 365,
        "equivalent_weeks_denominator": 7,
        "normalisation_kind": "analyst_assumption",
        "normalisation_basis": "Synthetic exact calendar-day/7 exposure scenario",
    }
    values.update(changes)
    return HoursHistoryRequest.model_validate(values)


def history(**changes: object) -> HistoricalHours:
    """Supply an explicit total for the entire selected window."""
    values: dict[str, object] = {
        "history_id": "history-1",
        "starts_on": date(2025, 11, 7),
        "ends_on": date(2026, 11, 7),
        "hours": Decimal(1500),
        "quantity_kind": "analyst_assumption",
        "basis": "Synthetic complete work history",
    }
    values.update(changes)
    return HistoricalHours.model_validate(values)


def test_full_calendar_window_retains_exact_history_maximum() -> None:
    """A twelve-month window is not silently replaced by fifty-two weeks."""
    result = select_normal_hours(rule(), request(), (history(),))
    assert_that(result.window_start == date(2025, 11, 7))
    assert_that(result.window_kind == "preceding_12_months")
    assert_that(result.history_hours_per_week == Fraction(2100, 73))
    assert_that(result.selected_hours_per_week == result.history_hours_per_week)
    assert_that(result.selected_basis == "history")
    assert_that(result.equivalent_weeks == Fraction(365, 7))
    assert_that(result.history_hours_per_week != Fraction(1500, 52))


def test_short_eligible_service_uses_entire_service_window() -> None:
    """The exact forty-week boundary admits the shorter-history branch."""
    leave = date(2026, 11, 7)
    start = leave - timedelta(weeks=40)
    data = request(
        continuous_service_from=start,
        equivalent_weeks_numerator=40,
        equivalent_weeks_denominator=1,
    )
    result = select_normal_hours(
        rule(),
        data,
        (history(starts_on=start, hours=Decimal(1200)),),
    )
    assert_that(result.window_start == start)
    assert_that(result.window_kind == "eligible_service_under_12_months")
    assert_that(result.selected_hours_per_week == Fraction(30))
    with pytest.raises(ValueError, match="service"):
        select_normal_hours(
            rule(),
            data.model_copy(
                update={"continuous_service_from": start + timedelta(days=1)},
            ),
            (history(starts_on=start),),
        )


def test_current_hours_and_tie_keep_both_comparands() -> None:
    """A lower historical mean is not added to the current-hours base."""
    result = select_normal_hours(
        rule(),
        request(current_hours_per_week=Decimal(35)),
        (history(),),
    )
    assert_that(result.selected_basis == "commencement")
    assert_that(result.selected_hours_per_week == Fraction(35))
    tied = select_normal_hours(
        rule(),
        request(
            equivalent_weeks_numerator=50,
            equivalent_weeks_denominator=1,
            current_hours_per_week=Decimal(30),
        ),
        (history(),),
    )
    assert_that(tied.selected_basis == "tie")
    assert_that(
        tied.history_hours_per_week == tied.current_hours_per_week == Fraction(30),
    )


def test_segmentation_order_and_decimal_precision_preserve_result() -> None:
    """A complete partition carries the same exact aggregate as the whole window."""
    split = date(2026, 5, 1)
    rows = (
        history(ends_on=split, hours=Decimal(700)),
        history(history_id="history-2", starts_on=split, hours=Decimal(800)),
    )
    with localcontext() as ctx:
        ctx.prec = 3
        result = select_normal_hours(rule(), request(), tuple(reversed(rows)))
    assert_that(
        result.selected_hours_per_week
        == select_normal_hours(rule(), request(), (history(),)).selected_hours_per_week,
    )
    assert_that(result.rows == rows)


@pytest.mark.parametrize(
    "rows",
    [
        (),
        (history(starts_on=date(2025, 11, 8)),),
        (history(ends_on=date(2026, 11, 6)),),
        (history(), history()),
        (
            history(ends_on=date(2026, 5, 2)),
            history(history_id="other", starts_on=date(2026, 5, 1)),
        ),
        (
            history(ends_on=date(2026, 5, 1)),
            history(history_id="other", starts_on=date(2026, 5, 2)),
        ),
    ],
)
def test_missing_overlapping_or_duplicate_history_is_not_zero(
    rows: tuple[HistoricalHours, ...],
) -> None:
    """An affirmative assertion alone cannot cover an incomplete timeline."""
    with pytest.raises(ValueError, match=r"history|History|Duplicate"):
        select_normal_hours(rule(), request(), rows)


def test_explicit_zero_history_is_valid_and_retained() -> None:
    """Known zero hours differs from an absent history row."""
    result = select_normal_hours(
        rule(),
        request(current_hours_per_week=Decimal(0)),
        (history(hours=Decimal(0)),),
    )
    assert_that(result.selected_hours_per_week == 0)
    assert_that(result.selected_basis == "tie")


@pytest.mark.parametrize(
    "changes",
    [
        {"history_complete": False},
        {"continuous_service_verified": False},
        {"normalisation_basis": " "},
        {"equivalent_weeks_numerator": 0},
        {"equivalent_weeks_denominator": 0},
        {"current_hours_per_week": Decimal("NaN")},
    ],
)
def test_missing_review_or_invalid_exposure_fails(changes: dict[str, object]) -> None:
    """No unreviewed denominator or hidden missing-service default is allowed."""
    with pytest.raises(ValueError, match=r"history|service|basis|greater|finite"):
        request(**changes)


def test_rule_and_source_admission_survive_unchecked_model_copies() -> None:
    """The hours selector admits the exact reviewed source scope and date."""
    for changes, expected in [
        ({"reviewed": False}, "review"),
        ({"source_sha256": "b" * 64}, "hash"),
        ({"employer": "Other"}, "scope"),
        ({"effective_to": date(2026, 11, 7)}, "date"),
    ]:
        copied = rule().model_copy(update=changes)
        with pytest.raises(ValueError, match=expected):
            select_normal_hours(copied, request(), (history(),))


def test_calendar_anniversary_requires_explicit_leap_day_convention() -> None:
    """The selected clamp method handles the preceding non-leap anniversary."""
    rules = rule(
        effective_from=date(2024, 1, 1),
        effective_to=date(2025, 1, 1),
        sources=SourceRegistry(records=(source(effective_from=date(2024, 1, 1)),)),
    )
    data = request(
        leave_starts_on=date(2024, 2, 29),
        continuous_service_from=date(2022, 1, 1),
        equivalent_weeks_numerator=366,
        equivalent_weeks_denominator=7,
    )
    rows = (
        history(
            starts_on=date(2023, 2, 28),
            ends_on=date(2024, 2, 29),
            hours=Decimal(1500),
        ),
    )
    result = select_normal_hours(rules, data, rows)
    assert_that(result.window_start == date(2023, 2, 28))
    assert_that(result.equivalent_weeks == Fraction(366, 7))


def test_exact_service_anniversary_uses_twelve_month_history() -> None:
    """The anniversary boundary is inclusive for the longer-service branch."""
    data = request(continuous_service_from=date(2025, 11, 7))
    result = select_normal_hours(rule(), data, (history(),))
    assert_that(result.window_kind == "preceding_12_months")


def test_source_knowledge_and_unresolved_applicability_are_rejected() -> None:
    """A held document alone cannot qualify the chosen hours rule."""
    for record, expected in [
        (source(applicability="unresolved"), "scope"),
        (source(retrieved_at=datetime(2026, 12, 1, tzinfo=UTC)), "knowledge"),
    ]:
        rules = rule(sources=SourceRegistry(records=(record,)))
        with pytest.raises(ValueError, match=expected):
            select_normal_hours(rules, request(), (history(),))


def test_invalid_history_copies_and_service_intervals_are_rejected() -> None:
    """Revalidate quantity/interval inputs rather than trusting model copies."""
    bad = history().model_copy(update={"hours": Decimal(-1)})
    with pytest.raises(ValueError, match="greater"):
        select_normal_hours(rule(), request(), (bad,))
    with pytest.raises(ValueError, match="nonempty"):
        history(ends_on=date(2025, 11, 7))
    with pytest.raises(ValueError, match="service"):
        request(continuous_service_from=date(2026, 11, 7))
