# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Compare complete alternative wage totals without inventing actual payroll."""

from datetime import date, datetime, timedelta
from decimal import Decimal, localcontext
from fractions import Fraction
from zoneinfo import ZoneInfo

import pytest

from src.annualised_pay import (
    AnnualisedPayRequest,
    AnnualisedPayRule,
    ReviewSettlement,
    WagePeriodEvidence,
    compare_annualised_pay,
)
from src.pay_period_effective import PeriodCalendar
from src.source_registry import SourceRegistry
from tests.checks import assert_that
from tests.test_source_registry import source


def rule(**changes: object) -> AnnualisedPayRule:
    """Declare a reviewed synthetic six-fortnight comparison scope."""
    values: dict[str, object] = {
        "rule_id": "synthetic-comparison",
        "currency": "AUD",
        "comparison_periods": 6,
        "period_unit": "fortnight",
        "annualised_components": ("annualised_salary",),
        "agreement_components": ("salary", "premium"),
        "component_basis": "Synthetic complete comparison-component declarations",
        "local_timezone": "Australia/Sydney",
        "as_known_on": date(2026, 11, 7),
        "source_id": "synthetic-award-1",
        "source_sha256": "a" * 64,
        "citation": "Synthetic full-window wage comparison",
        "reviewed": True,
        "effective_from": date(2026, 1, 1),
        "effective_to": date(2027, 1, 1),
        "jurisdiction": "QLD",
        "employer": "Synthetic employer",
        "classification": "Synthetic grade",
        "sources": SourceRegistry(records=(source(),)),
    }
    values.update(changes)
    return AnnualisedPayRule.model_validate(values)


def calendar(start: datetime | None = None) -> PeriodCalendar:
    """Supply the complete calendar rather than guessing a comparison duration."""
    first = start or datetime(2026, 1, 1, tzinfo=ZoneInfo("Australia/Sydney"))
    return PeriodCalendar(
        calendar_id="synthetic-pay-calendar",
        complete=True,
        boundaries=tuple(first + timedelta(weeks=2 * i) for i in range(7)),
    )


def request(**changes: object) -> AnnualisedPayRequest:
    """Keep eligibility/history assertions and pending settlement separate."""
    values: dict[str, object] = {
        "case_id": "opaque-case",
        "calendar": calendar(),
        "eligibility_verified": True,
        "eligibility_basis": "Synthetic annualised scenario",
        "earnings_complete": True,
        "review_requested": True,
        "settlement": None,
    }
    values.update(changes)
    return AnnualisedPayRequest.model_validate(values)


def earnings(c: PeriodCalendar | None = None) -> tuple[WagePeriodEvidence, ...]:
    """Declare every component, known zeros, source hashes and economic period."""
    c = c or calendar()
    return tuple(
        WagePeriodEvidence(
            period_id=f"pay-{i}",
            starts_at=a,
            ends_at=b,
            currency="AUD",
            annualised={"annualised_salary": Fraction(1000)},
            agreement={"salary": Fraction(950), "premium": Fraction(50)},
            annualised_kind="analyst_assumption",
            agreement_kind="analyst_assumption",
            annualised_evidence_id="synthetic-pay",
            annualised_evidence_sha256="b" * 64,
            agreement_evidence_id="synthetic-alternative",
            agreement_evidence_sha256="c" * 64,
            annualised_known_on=date(2026, 11, 7),
            agreement_known_on=date(2026, 11, 7),
            basis="Complete synthetic period evidence, not a payroll observation",
        )
        for i, (a, b) in enumerate(zip(c.boundaries, c.boundaries[1:], strict=False))
    )


def test_whole_window_nets_losing_periods_before_shortfall() -> None:
    """One 200 gain and one 200 loss cancel; per-period floors would invent a topup."""
    rows = list(earnings())
    rows[0] = rows[0].model_copy(
        update={"agreement": {"salary": Fraction(1150), "premium": Fraction(50)}},
    )
    rows[1] = rows[1].model_copy(
        update={"agreement": {"salary": Fraction(750), "premium": Fraction(50)}},
    )
    result = compare_annualised_pay(rule(), request(), tuple(rows))
    assert_that(result.annualised_total == result.agreement_total == Fraction(6000))
    assert_that(result.shortfall == 0)
    assert_that(result.payment_period is None)
    assert_that(
        [r.net_difference for r in result.rows][:2] == [Fraction(200), Fraction(-200)],
    )


def test_exact_positive_shortfall_and_pending_payment() -> None:
    """A repeating rational amount survives low Decimal precision and JSON."""
    rows = list(earnings())
    rows[0] = rows[0].model_copy(
        update={"agreement": {"salary": Fraction(950), "premium": Fraction(151, 3)}},
    )
    parsed = tuple(
        WagePeriodEvidence.model_validate_json(r.model_dump_json()) for r in rows
    )
    with localcontext() as ctx:
        ctx.prec = 3
        result = compare_annualised_pay(rule(), request(), parsed)
    assert_that(result.shortfall == Fraction(1, 3))
    assert_that(result.minimum_total == Fraction(18001, 3))
    assert_that(result.payment_period is None)
    assert_that(result.mode == "scenario")


def positive_rows() -> tuple[WagePeriodEvidence, ...]:
    """Supply a complete scenario with one exact 100 shortfall over the window."""
    rows = list(earnings())
    rows[0] = rows[0].model_copy(
        update={"agreement": {"salary": Fraction(1050), "premium": Fraction(50)}},
    )
    return tuple(rows)


def settlement(*, at_boundary: bool = False) -> ReviewSettlement:
    """Declare the strict next-start convention and a complete future calendar."""
    start = calendar().boundaries[-1].astimezone(ZoneInfo("Australia/Sydney"))
    c = PeriodCalendar(
        calendar_id="settlement-calendar",
        complete=True,
        boundaries=tuple(start + timedelta(weeks=2 * i) for i in range(3)),
    )
    return ReviewSettlement(
        completed_at=start if at_boundary else start + timedelta(days=3),
        calendar=c,
        boundary_method="first_period_start_strictly_after_review",
        convention_kind="analyst_assumption",
        convention_basis="Explicit strict-after synthetic convention",
    )


@pytest.mark.parametrize("at_boundary", [False, True])
def test_completed_review_selects_next_complete_period(*, at_boundary: bool) -> None:
    """A review at a boundary does not silently select that already-started period."""
    review = settlement(at_boundary=at_boundary)
    result = compare_annualised_pay(rule(), request(settlement=review), positive_rows())
    assert_that(result.shortfall == Fraction(100))
    assert_that(result.minimum_total == Fraction(6100))
    assert_that(result.payment_period == tuple(review.calendar.boundaries[1:]))
    assert_that(result.request.settlement == review)


def test_unrequested_review_retains_comparison_but_no_payment_period() -> None:
    """Potential shortfall can be valued without claiming a completed review."""
    result = compare_annualised_pay(
        rule(),
        request(review_requested=False),
        positive_rows(),
    )
    assert_that(result.shortfall == Fraction(100))
    assert_that(result.payment_period is None)
    with pytest.raises(ValueError, match="review request"):
        request(review_requested=False, settlement=settlement())


def test_reordering_input_does_not_change_calendar_order_or_totals() -> None:
    """Stable economic intervals, not incoming list order, define the ledger."""
    rows = positive_rows()
    result = compare_annualised_pay(rule(), request(), tuple(reversed(rows)))
    assert_that(
        [r.evidence.period_id for r in result.rows] == [r.period_id for r in rows],
    )
    assert_that(result.shortfall == Fraction(100))


def test_fortnights_follow_local_calendar_through_dst() -> None:
    """The fall-back fortnight is longer in UTC without changing its period count."""
    c = calendar(datetime(2026, 3, 12, tzinfo=ZoneInfo("Australia/Sydney")))
    result = compare_annualised_pay(rule(), request(calendar=c), earnings(c))
    assert_that(result.shortfall == 0)
    assert_that(
        any(
            (b - a) != timedelta(weeks=2)
            for a, b in zip(c.boundaries, c.boundaries[1:], strict=False)
        ),
    )


@pytest.mark.parametrize(
    "case",
    [
        "missing",
        "duplicate_interval",
        "duplicate_id",
        "missing_component",
        "extra_component",
        "currency",
        "knowledge",
    ],
)
def test_incomplete_or_incompatible_wage_evidence_is_rejected(case: str) -> None:
    """Missing fields do not become zero or disappear from either comparison side."""
    rows = list(earnings())
    if case == "missing":
        rows.pop()
    elif case == "duplicate_interval":
        rows[1] = rows[0]
    elif case == "duplicate_id":
        rows[1] = rows[1].model_copy(update={"period_id": rows[0].period_id})
    elif case == "missing_component":
        rows[0] = rows[0].model_copy(update={"agreement": {"salary": Fraction(950)}})
    elif case == "extra_component":
        rows[0] = rows[0].model_copy(
            update={
                "agreement": {
                    "salary": Fraction(950),
                    "premium": Fraction(50),
                    "extra": Fraction(0),
                },
            },
        )
    elif case == "currency":
        rows[0] = rows[0].model_copy(update={"currency": "EUR"})
    else:
        rows[0] = rows[0].model_copy(update={"agreement_known_on": date(2026, 11, 8)})
    with pytest.raises(ValueError, match=r"record|component|currency|knowledge"):
        compare_annualised_pay(rule(), request(), tuple(rows))


@pytest.mark.parametrize("case", ["hash", "scope", "coverage", "knowledge"])
def test_rule_source_admission_is_required(case: str) -> None:
    """Rule review alone cannot substitute for exact source scope/hash/time."""
    changes: dict[str, object] = {}
    if case == "hash":
        changes["source_sha256"] = "d" * 64
    elif case == "scope":
        changes["employer"] = "Different employer"
    elif case == "coverage":
        changes["effective_from"] = date(2026, 2, 1)
    else:
        changes["as_known_on"] = date(2025, 12, 31)
    with pytest.raises(ValueError, match=r"hash|scope|cover|knowledge"):
        compare_annualised_pay(rule(**changes), request(), earnings())


@pytest.mark.parametrize(
    "case",
    [
        "too_few_periods",
        "non_fortnight",
        "early_review",
        "missing_next_period",
        "future_review",
    ],
)
def test_calendar_and_review_boundaries_fail_closed(case: str) -> None:
    """Incomplete calendars and prematurely completed reviews cannot select cash."""
    r = request()
    if case == "too_few_periods":
        r = request(
            calendar=calendar().model_copy(
                update={"boundaries": calendar().boundaries[:-1]},
            ),
        )
    elif case == "non_fortnight":
        points = list(calendar().boundaries)
        points[1] += timedelta(hours=1)
        r = request(
            calendar=calendar().model_copy(update={"boundaries": tuple(points)}),
        )
    else:
        review = settlement()
        if case == "early_review":
            review = review.model_copy(
                update={"completed_at": calendar().boundaries[0]},
            )
        elif case == "missing_next_period":
            review = review.model_copy(
                update={
                    "calendar": review.calendar.model_copy(
                        update={"boundaries": review.calendar.boundaries[:2]},
                    ),
                },
            )
        else:
            review = review.model_copy(
                update={
                    "completed_at": datetime(
                        2027,
                        1,
                        1,
                        tzinfo=ZoneInfo("Australia/Sydney"),
                    ),
                },
            )
        r = request(settlement=review)
    with pytest.raises(ValueError, match=r"period|fortnight|window|knowledge"):
        compare_annualised_pay(rule(), r, positive_rows())


def test_known_zero_components_and_observed_mode_are_retained() -> None:
    """An explicit zero is valid; observed labels retain their evidence identities."""
    rows = tuple(
        r.model_copy(
            update={
                "annualised_kind": "observed_pay",
                "agreement_kind": "reviewed_counterfactual",
                "agreement": {"salary": Fraction(1000), "premium": Fraction(0)},
            },
        )
        for r in earnings()
    )
    result = compare_annualised_pay(rule(), request(), rows)
    assert_that(result.mode == "reviewed_pay_records")
    assert_that(result.rows[0].evidence.agreement["premium"] == 0)
    assert_that(result.rows[0].evidence.annualised_evidence_sha256 == "b" * 64)


def test_forged_negative_or_null_amounts_are_not_accepted() -> None:
    """Revalidation catches nested model-copy changes before arithmetic."""
    for amount in (Decimal(-1), None):
        rows = list(earnings())
        rows[0] = rows[0].model_copy(
            update={"annualised": {"annualised_salary": amount}},
        )
        with pytest.raises(ValueError, match=r"greater than|instance|valid|input"):
            compare_annualised_pay(rule(), request(), tuple(rows))


def test_late_source_retrieval_and_naive_review_are_rejected() -> None:
    """Document knowledge and review instants require their own evidence checks."""
    late = SourceRegistry(
        records=(
            source(
                retrieved_at=datetime(2026, 11, 8, tzinfo=ZoneInfo("UTC")),
            ),
        ),
    )
    with pytest.raises(ValueError, match="knowledge"):
        compare_annualised_pay(rule(sources=late), request(), earnings())
    review = settlement().model_copy(
        update={
            "completed_at": datetime(2026, 4, 1, tzinfo=ZoneInfo("UTC")).replace(
                tzinfo=None,
            ),
        },
    )
    with pytest.raises(ValueError, match="timezone aware"):
        compare_annualised_pay(rule(), request(settlement=review), positive_rows())


@pytest.mark.parametrize("field", ["eligibility_verified", "earnings_complete"])
def test_missing_case_qualification_fails_before_pricing(field: str) -> None:
    """A complete mathematical ledger does not establish individual eligibility."""
    with pytest.raises(ValueError, match="eligibility and complete"):
        request(**{field: False})
