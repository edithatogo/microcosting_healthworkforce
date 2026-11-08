# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Keep paid absence, payment exposure, accrual and entitlement debits distinct."""

from datetime import date, timedelta
from decimal import Decimal
from fractions import Fraction

import pytest

from src.historical_hours import select_normal_hours
from src.normal_pay import price_selected_hours
from src.paid_leave import (
    PaidLeavePolicy,
    PaidLeaveRequest,
    PaidLeaveSchedule,
    build_paid_leave,
)
from src.source_registry import SourceRegistry
from tests.checks import assert_that
from tests.test_historical_hours import (
    history as hours_history,
)
from tests.test_historical_hours import (
    request as hours_request,
)
from tests.test_historical_hours import (
    rule as hours_rule,
)
from tests.test_normal_pay import exposure, prices
from tests.test_source_registry import source
from tests.test_unit_quotes import quote, release
lazy from src.unit_quotes import UnitQuoteRelease


def policy(**changes: object) -> PaidLeavePolicy:
    """Use a synthetic reviewed profile with scoped source evidence."""
    values: dict[str, object] = {
        "policy_id": "synthetic-primary",
        "full_pay_weeks": 18,
        "half_pay_available": True,
        "advance_available": True,
        "paid_accrual_limit_weeks": 18,
        "maximum_absence_weeks": 52,
        "entitlement_budget_weeks": 52,
        "source_id": "synthetic-award-1",
        "source_sha256": "a" * 64,
        "citation": "Synthetic paid leave clauses",
        "effective_from": date(2026, 1, 1),
        "effective_to": date(2028, 1, 1),
        "as_known_on": date(2026, 11, 7),
        "reviewed": True,
        "jurisdiction": "QLD",
        "employer": "Synthetic employer",
        "classification": "Synthetic grade",
        "sources": SourceRegistry(records=(source(verified_through=date(2028, 1, 1)),)),
    }
    values.update(changes)
    return PaidLeavePolicy.model_validate(values)


def request(**changes: object) -> PaidLeaveRequest:
    """Require explicit approval, convention and unknown offset/accrual choices."""
    start = date(2026, 2, 1)
    values: dict[str, object] = {
        "starts_on": start,
        "approved_ends_on": start + timedelta(weeks=52),
        "payment_mode": "full",
        "advance_payment_on": None,
        "eligibility_verified": True,
        "approval_verified": True,
        "eligibility_basis": "Synthetic eligible route; no real employee",
        "approval_basis": "Synthetic approved absence",
        "employment_basis": "ongoing",
        "contract_ends_on": None,
        "calendar_method": "calendar_days_over_seven_v1",
        "calendar_basis": "Explicit synthetic calendar-week exposure convention",
        "offset_basis": "unresolved",
        "offset_review_kind": "unresolved",
        "offset_rationale": "Half-pay entitlement debit remains unqualified",
        "unpaid_accrual_factor": None,
        "unpaid_accrual_review_kind": "unresolved",
        "unpaid_accrual_basis": "Working-day accrual treatment unreviewed",
        "split_on": (),
    }
    values.update(changes)
    return PaidLeaveRequest.model_validate(values)


def test_full_and_half_keep_equal_payment_but_different_absence() -> None:
    """Eighteen full-pay weeks and thirty-six half-pay weeks remain separate axes."""
    full = build_paid_leave(policy(), request())
    half = build_paid_leave(policy(), request(payment_mode="half"))
    assert_that(
        full.salary_equivalent_weeks == half.salary_equivalent_weeks == Fraction(18),
    )
    assert_that(full.paid_absence_weeks == Fraction(18))
    assert_that(half.paid_absence_weeks == Fraction(36))
    assert_that(full.unpaid_absence_weeks == Fraction(34))
    assert_that(half.unpaid_absence_weeks == Fraction(16))
    assert_that(
        full.known_accrual_exposure_weeks
        == half.known_accrual_exposure_weeks
        == Fraction(18),
    )
    assert_that(
        full.accrual_exposure_weeks is None and half.accrual_exposure_weeks is None,
    )
    assert_that(half.paid_entitlement_debit_weeks is None)
    assert_that(half.remaining_debit_budget_weeks is None)


def test_half_pay_tail_has_no_extra_paid_accrual() -> None:
    """Half pay does not turn the entire paid duration into accruing exposure."""
    start = date(2026, 2, 1)
    result = build_paid_leave(
        policy(),
        request(payment_mode="half", approved_ends_on=start + timedelta(weeks=36)),
    )
    assert_that(result.accrual_exposure_weeks == Fraction(18))
    assert_that(result.rows[0].salary_equivalent_weeks == Fraction(9))
    assert_that(result.rows[1].salary_equivalent_weeks == Fraction(9))
    assert_that(result.rows[1].accrual_exposure_weeks == 0)


def test_advance_instruction_does_not_change_absence_or_accrual() -> None:
    """A supplied cash instruction is distinct from the economic exposure ledger."""
    result = build_paid_leave(
        policy(),
        request(payment_mode="advance", advance_payment_on=date(2026, 1, 31)),
    )
    ordinary = build_paid_leave(policy(), request())
    assert_that(result.rows == ordinary.rows)
    instruction = result.advance_instruction
    if instruction is None:
        pytest.fail("Advance mode requires a separate timing instruction")
    assert_that(instruction.full_pay_equivalent_weeks == Fraction(18))
    assert_that(instruction.payment_on == date(2026, 1, 31))
    assert_that(ordinary.advance_instruction is None)


@pytest.mark.parametrize(
    ("basis", "debit", "remaining"),
    [("calendar_absence", 36, 0), ("full_pay_equivalent", 18, 18)],
)
def test_offset_scenarios_are_explicit_not_inferred(
    basis: str,
    debit: int,
    remaining: int,
) -> None:
    """Alternative debit interpretations carry their own declared review basis."""
    result = build_paid_leave(
        policy(),
        request(
            payment_mode="half",
            offset_basis=basis,
            offset_review_kind="analyst_assumption",
            offset_rationale="Explicit sensitivity, not accepted legal interpretation",
        ),
    )
    assert_that(result.paid_entitlement_debit_weeks == Fraction(debit))
    assert_that(result.remaining_debit_budget_weeks == Fraction(remaining))


def test_explicit_unpaid_accrual_and_unknown_paid_limit() -> None:
    """Unknown accrual is not zero; a supplied factor keeps its own basis."""
    known = build_paid_leave(
        policy(),
        request(
            unpaid_accrual_factor=Fraction(0),
            unpaid_accrual_review_kind="analyst_assumption",
            unpaid_accrual_basis="Explicit synthetic no-accrual scenario",
        ),
    )
    assert_that(known.accrual_exposure_weeks == Fraction(18))
    unknown = build_paid_leave(policy(paid_accrual_limit_weeks=None), request())
    assert_that(unknown.accrual_exposure_weeks is None)
    assert_that(unknown.known_accrual_exposure_weeks == 0)


def test_explicit_splits_preserve_all_exposure_totals_and_unknowns() -> None:
    """Price/calendar split points do not create extra leave or pay."""
    plain = build_paid_leave(policy(), request(payment_mode="half"))
    split = build_paid_leave(
        policy(),
        request(payment_mode="half", split_on=(date(2026, 7, 1), date(2026, 3, 15))),
    )
    assert_that(split.salary_equivalent_weeks == plain.salary_equivalent_weeks)
    assert_that(split.paid_absence_weeks == plain.paid_absence_weeks)
    assert_that(
        split.known_accrual_exposure_weeks == plain.known_accrual_exposure_weeks,
    )
    assert_that(split.accrual_exposure_weeks is None)


def test_approved_shortening_and_contract_limit_keep_unused_budget() -> None:
    """Only the explicitly approved end truncates exposure; contract overrun fails."""
    end = date(2026, 3, 1)
    shortened = request(
        approved_ends_on=end,
        employment_basis="fixed_term",
        contract_ends_on=end,
    )
    result = build_paid_leave(policy(), shortened)
    assert_that(result.salary_equivalent_weeks == Fraction(4))
    assert_that(result.unused_salary_equivalent_weeks == Fraction(14))
    with pytest.raises(ValueError, match="contract"):
        request(employment_basis="fixed_term", contract_ends_on=end)


@pytest.mark.parametrize(
    "changes",
    [
        {"eligibility_verified": False},
        {"approval_verified": False},
        {"employment_basis": "fixed_term"},
        {"offset_basis": "calendar_absence"},
        {"advance_payment_on": date(2026, 1, 31)},
        {"payment_mode": "advance"},
        {"payment_mode": "advance", "advance_payment_on": date(2026, 2, 1)},
        {"unpaid_accrual_factor": Fraction(2)},
        {"split_on": (date(2026, 3, 1), date(2026, 3, 1))},
    ],
)
def test_invalid_declarations_are_rejected(changes: dict[str, object]) -> None:
    """Unsupported or incomplete decisions cannot become hidden defaults."""
    with pytest.raises(
        ValueError,
        match=r"eligib|approval|contract|offset|advance|factor|equal|split",
    ):
        request(**changes)


def test_policy_source_dates_and_caps_are_enforced_after_copy() -> None:
    """Source, profile and date failures remain visible even for copied objects."""
    for changes, expected in [
        ({"source_sha256": "b" * 64}, "hash"),
        ({"reviewed": False}, "review"),
        ({"half_pay_available": False}, "half"),
        ({"maximum_absence_weeks": 40}, "limit"),
        ({"effective_to": date(2026, 3, 1)}, "date"),
    ]:
        with pytest.raises(ValueError, match=expected):
            build_paid_leave(
                policy().model_copy(update=changes),
                request(payment_mode="half"),
            )


def test_zero_debit_budget_cannot_hide_known_overdraw() -> None:
    """An explicitly resolved debit must fit the declared entitlement budget."""
    with pytest.raises(ValueError, match="budget"):
        build_paid_leave(
            policy(entitlement_budget_weeks=0),
            request(
                offset_basis="calendar_absence",
                offset_review_kind="analyst_assumption",
            ),
        )


def test_advance_option_and_source_knowledge_require_admission() -> None:
    """A timing instruction still needs the admitted profile and source horizon."""
    data = request(payment_mode="advance", advance_payment_on=date(2026, 1, 31))
    with pytest.raises(ValueError, match="advance"):
        build_paid_leave(policy(advance_available=False), data)
    with pytest.raises(ValueError, match="date"):
        build_paid_leave(
            policy(),
            request(payment_mode="advance", advance_payment_on=date(2025, 12, 31)),
        )
    late = policy(as_known_on=date(2025, 12, 31))
    with pytest.raises(ValueError, match="knowledge"):
        build_paid_leave(late, request())
    unresolved = policy(
        sources=SourceRegistry(records=(source(applicability="unresolved"),)),
    )
    with pytest.raises(ValueError, match="scope"):
        build_paid_leave(unresolved, request())


def test_unknown_and_fractional_accrual_roundtrip_is_explicit() -> None:
    """Rational accrual factors survive JSON and strict copied-input checks."""
    data = request(
        unpaid_accrual_factor=Fraction(1, 2),
        unpaid_accrual_review_kind="analyst_assumption",
        unpaid_accrual_basis="Explicit synthetic half-accrual scenario",
    )
    restored = PaidLeaveRequest.model_validate_json(data.model_dump_json())
    result = build_paid_leave(policy(), restored)
    assert_that(result.accrual_exposure_weeks == Fraction(35))
    with pytest.raises(ValueError, match=r"instance|Decimal"):
        build_paid_leave(
            policy(),
            data.model_copy(update={"unpaid_accrual_factor": 0.5}),
        )


def test_exact_paid_boundary_and_outside_splits_are_rejected() -> None:
    """A fully paid approved period does not invent an unpaid tail."""
    start = date(2026, 2, 1)
    result = build_paid_leave(
        policy(),
        request(approved_ends_on=start + timedelta(weeks=18)),
    )
    assert_that(result.unpaid_absence_weeks == 0)
    assert_that(result.accrual_exposure_weeks == Fraction(18))
    with pytest.raises(ValueError, match="split"):
        request(split_on=(start,))


def test_shortened_half_pay_keeps_normal_pay_equivalent_budget() -> None:
    """Four calendar weeks at half pay use two normal-pay-equivalent weeks."""
    result = build_paid_leave(
        policy(),
        request(payment_mode="half", approved_ends_on=date(2026, 3, 1)),
    )
    assert_that(result.salary_equivalent_weeks == Fraction(2))
    assert_that(result.unused_salary_equivalent_weeks == Fraction(16))
    assert_that(result.accrual_exposure_weeks == Fraction(4))


def salary_cost(schedule: PaidLeaveSchedule, rates: UnitQuoteRelease) -> Fraction:
    """Independently bind complete paid rows to explicit synthetic price columns."""
    selected = select_normal_hours(
        hours_rule(),
        hours_request(leave_starts_on=date(2026, 2, 1)),
        (hours_history(starts_on=date(2025, 2, 1), ends_on=date(2026, 2, 1)),),
    )
    total = Fraction(0)
    for row in schedule.rows:
        if row.kind != "paid":
            continue
        candidates = [
            q
            for q in rates.quotes
            if q.component == "salary"
            and q.starts_on <= row.starts_on
            and row.ends_on <= q.ends_on
        ]
        assert_that(len(candidates) == 1)
        data = exposure(
            quantity_id=row.starts_on.isoformat(),
            quote_id=candidates[0].quote_id,
            week_quantity=row.salary_equivalent_weeks,
            valued_on=row.starts_on,
        )
        total += price_selected_hours(rates, selected, data, ()).pricing.total
    return total


def test_constant_price_full_half_and_advance_reduce_to_same_salary_exposure() -> None:
    """Separate calendar/payment profiles retain the constant-price identity."""
    full = build_paid_leave(policy(), request())
    half = build_paid_leave(policy(), request(payment_mode="half"))
    advance = build_paid_leave(
        policy(),
        request(payment_mode="advance", advance_payment_on=date(2026, 1, 31)),
    )
    rates = prices()
    expected = Fraction(1134000, 73)
    assert_that(
        salary_cost(full, rates)
        == salary_cost(half, rates)
        == salary_cost(advance, rates)
        == expected,
    )


def test_wage_change_distinguishes_full_and_half_payment_exposure() -> None:
    """Equal normal-pay-equivalent weeks do not imply equal dated price costs."""
    rates = release(
        quote(
            quote_id="salary",
            component="salary",
            unit="hour",
            amount=Decimal(30),
            ends_on=date(2026, 7, 1),
        ),
        quote(
            quote_id="salary-later",
            component="salary",
            unit="hour",
            amount=Decimal(35),
            starts_on=date(2026, 7, 1),
        ),
    ).model_copy(update={"as_known_on": date(2026, 11, 7)})
    full = build_paid_leave(policy(), request(split_on=(date(2026, 7, 1),)))
    half = build_paid_leave(
        policy(),
        request(payment_mode="half", split_on=(date(2026, 7, 1),)),
    )
    assert_that(salary_cost(full, rates) == Fraction(1134000, 73))
    assert_that(salary_cost(half, rates) == Fraction(1210500, 73))
    assert_that(
        salary_cost(half, rates) - salary_cost(full, rates) == Fraction(76500, 73),
    )


def test_unpaid_accrual_value_cannot_hide_unresolved_review() -> None:
    """Unknown treatment cannot become a numeric factor through a missing review."""
    with pytest.raises(ValueError, match="accrual factor"):
        request(unpaid_accrual_factor=Fraction(0))
    with pytest.raises(ValueError, match="accrual factor"):
        request(unpaid_accrual_review_kind="source_reviewed")


def test_four_week_budget_at_half_pay_preserves_eight_weeks_of_absence() -> None:
    """Keep eight approved weeks of absence and four weeks of salary exposure."""
    start = date(2026, 2, 1)
    result = build_paid_leave(
        policy(full_pay_weeks=4),
        request(
            starts_on=start,
            approved_ends_on=start + timedelta(weeks=8),
            payment_mode="half",
        ),
    )
    assert_that(result.paid_absence_weeks == Fraction(8))
    assert_that(result.salary_equivalent_weeks == Fraction(4))
    assert_that(result.unpaid_absence_weeks == 0)
    assert_that(result.paid_entitlement_debit_weeks is None)
    assert_that(salary_cost(result, prices()) == Fraction(252000, 73))


def test_unresolved_paid_debit_cannot_hide_unpaid_overdraw() -> None:
    """Known unpaid weeks exceed the budget under either paid-debit convention."""
    with pytest.raises(ValueError, match="budget"):
        build_paid_leave(policy(entitlement_budget_weeks=33), request())


def test_unresolved_half_pay_debit_checks_the_minimum_possible_budget() -> None:
    """Reject impossible budgets while preserving ambiguity for feasible ones."""
    half = request(payment_mode="half")
    with pytest.raises(ValueError, match="budget"):
        build_paid_leave(policy(entitlement_budget_weeks=33), half)
    result = build_paid_leave(policy(entitlement_budget_weeks=34), half)
    assert_that(result.paid_entitlement_debit_weeks is None)
    assert_that(result.remaining_debit_budget_weeks is None)
