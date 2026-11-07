# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Compose leave exposure with exact selected hours and dated source prices."""

from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Literal

import pytest

from src.leave_pricing import (
    LeaveLoadingComparison,
    LeaveLoadingMoneyCap,
    LeavePriceSelection,
    allocate_leave_loading_hours,
    combined_leave_hours,
    price_leave_loading,
    price_paid_leave,
    qualifying_shift_leave_credit,
    select_leave_loading_alternative,
)
from src.paid_leave import PaidLeaveSchedule, build_paid_leave
from tests.checks import assert_that
from tests.test_normal_pay import allowance, exposure, prices, selection
from tests.test_paid_leave import policy, request
from tests.test_unit_quotes import quote
lazy from src.leave_pricing import PricedLeave
lazy from src.unit_quotes import UnitQuoteRelease

START = date(2026, 11, 7)
MID = START + timedelta(weeks=1)
END = START + timedelta(weeks=2)


def schedule(mode: str = "half") -> PaidLeaveSchedule:
    """One full-pay-equivalent week over two approved calendar weeks."""
    return build_paid_leave(
        policy(full_pay_weeks=1, paid_accrual_limit_weeks=1),
        request(
            starts_on=START,
            approved_ends_on=END,
            payment_mode=mode,
            split_on=(MID,),
            advance_payment_on=START - timedelta(days=1) if mode == "advance" else None,
        ),
    )


def choices(
    leave: PaidLeaveSchedule,
    *,
    second_quote: str = "salary",
    mode: Literal["dated_row_start", "explicit_snapshot"] = "dated_row_start",
) -> tuple[LeavePriceSelection, ...]:
    """Select exact row exposures and a declared snapshot/dated method."""
    return tuple(
        LeavePriceSelection(
            starts_on=row.starts_on,
            ends_on=row.ends_on,
            valuation_method=mode,
            valuation_basis="Synthetic explicit valuation scenario",
            pricing=exposure(
                quantity_id=f"row-{i}",
                quote_id="salary" if i == 0 else second_quote,
                week_quantity=row.salary_equivalent_weeks,
                valued_on=row.starts_on if mode == "dated_row_start" else START,
            ),
            allowances=(),
        )
        for i, row in enumerate(leave.rows)
    )


def dated_prices() -> UnitQuoteRelease:
    """Declare an hourly price change without inferring allowance proration."""
    old = quote(
        quote_id="salary",
        component="salary",
        unit="hour",
        amount=Decimal(30),
        ends_on=MID,
    )
    new = quote(
        quote_id="salary-new",
        component="salary",
        unit="hour",
        amount=Decimal(40),
        starts_on=MID,
    )
    return prices().model_copy(update={"quotes": (old, new)})


def test_dated_half_pay_retains_exact_cost_and_independent_state() -> None:
    """Half-week exposures at30/40 cost73500/73, unaffected by Decimal precision."""
    leave = schedule()
    with localcontext() as context:
        context.prec = 3
        result = price_paid_leave(
            dated_prices(),
            selection(),
            leave,
            choices(leave, second_quote="salary-new"),
        )
    assert_that(result.total == Fraction(73500, 73))
    assert_that(result.schedule == leave)
    assert_that(result.schedule.paid_entitlement_debit_weeks is None)
    assert_that(result.schedule.accrual_exposure_weeks == Fraction(1))
    assert_that(
        [r.pricing.pricing.rows[0].quantity.quantity for r in result.rows]
        == [Fraction(1050, 73)] * 2,
    )


def test_full_half_and_advance_share_constant_price_exposure() -> None:
    """An advance instruction adds no extra salary; unpaid exposure remains zero."""
    results: list[PricedLeave] = []
    for mode in ("full", "half", "advance"):
        leave = schedule(mode)
        results.append(price_paid_leave(prices(), selection(), leave, choices(leave)))
    assert_that([r.total for r in results] == [Fraction(63000, 73)] * 3)
    assert_that(results[0].schedule.accrual_exposure_weeks is None)
    assert_that(results[2].schedule.advance_instruction is not None)
    assert_that(results[0].rows[1].pricing.pricing.total == 0)


def test_snapshot_prices_can_explicitly_hold_prices_fixed() -> None:
    """A declared counterfactual differs from using a price outside its dated row."""
    leave = schedule()
    result = price_paid_leave(
        dated_prices(),
        selection(),
        leave,
        choices(leave, mode="explicit_snapshot"),
    )
    assert_that(result.total == Fraction(63000, 73))
    with pytest.raises(ValueError, match="cover"):
        price_paid_leave(dated_prices(), selection(), leave, choices(leave))


def test_allowances_keep_their_units_and_are_not_scaled_by_half_pay() -> None:
    """An explicitly supplied half-fortnight costs100.01/2 once on each row."""
    leave = schedule()
    selected = choices(leave)
    selected = tuple(
        c.model_copy(
            update={
                "allowances": (
                    allowance().model_copy(
                        update={
                            "quantity_id": f"allowance-{i}",
                            "valued_on": c.starts_on,
                        },
                    ),
                ),
            },
        )
        for i, c in enumerate(selected)
    )
    result = price_paid_leave(
        prices(quote(quote_id="development", component="development")),
        selection(),
        leave,
        selected,
    )
    assert_that(result.total == Fraction(63000, 73) + Fraction(10001, 100))
    duplicate = selected[1].model_copy(update={"allowances": selected[0].allowances})
    with pytest.raises(ValueError, match="quantity identity"):
        price_paid_leave(prices(), selection(), leave, (selected[0], duplicate))


def test_forged_totals_are_rebuilt_before_pricing() -> None:
    """Dataclass totals and rows never replace original policy/history evidence."""
    leave = schedule()
    forged = replace(leave, salary_equivalent_weeks=Fraction(999), rows=())
    result = price_paid_leave(prices(), selection(), forged, choices(leave))
    assert_that(result.schedule == leave)
    assert_that(result.total == Fraction(63000, 73))


@pytest.mark.parametrize("case", ["missing", "duplicate", "wrong_weeks", "wrong_date"])
def test_incomplete_or_mismatched_price_selections_fail(case: str) -> None:
    """No schedule segment can disappear or be priced with another exposure."""
    leave = schedule()
    selected = choices(leave)
    if case == "missing":
        selected = selected[:1]
    elif case == "duplicate":
        selected = (selected[0], selected[0])
    elif case == "wrong_weeks":
        selected = (
            selected[0].model_copy(
                update={
                    "pricing": selected[0].pricing.model_copy(
                        update={"week_quantity": Fraction(1)},
                    ),
                },
            ),
            selected[1],
        )
    else:
        selected = (
            selected[0].model_copy(
                update={
                    "pricing": selected[0].pricing.model_copy(
                        update={"valued_on": MID},
                    ),
                },
            ),
            selected[1],
        )
    with pytest.raises(ValueError, match=r"interval|equivalent|valuation"):
        price_paid_leave(prices(), selection(), leave, selected)


@pytest.mark.parametrize("case", ["scope", "knowledge", "commencement"])
def test_source_scope_knowledge_and_leave_start_must_match(case: str) -> None:
    """Individually valid inputs from different contexts cannot be combined."""
    leave = schedule()
    if case == "scope":
        changed = leave.policy.model_copy(update={"classification": "Different"})
        leave = replace(leave, policy=changed)
    elif case == "knowledge":
        leave = replace(
            leave,
            policy=leave.policy.model_copy(
                update={
                    "as_known_on": date(2026, 11, 8),
                },
            ),
        )
    else:
        leave = build_paid_leave(
            leave.policy,
            leave.request.model_copy(
                update={
                    "starts_on": START + timedelta(days=1),
                    "split_on": (),
                },
            ),
        )
    with pytest.raises(ValueError, match=r"scope|commencement"):
        price_paid_leave(prices(), selection(), leave, choices(leave))


def test_dated_price_boundary_requires_an_explicit_schedule_split() -> None:
    """A snapshot at the first day cannot hide a price change inside a row."""
    leave = build_paid_leave(
        schedule().policy.model_copy(update={"paid_accrual_limit_weeks": 2}),
        schedule().request.model_copy(
            update={"split_on": ()},
        ),
    )
    assert_that(len(leave.rows) == 1)
    with pytest.raises(ValueError, match="cover"):
        price_paid_leave(dated_prices(), selection(), leave, choices(leave))


def test_constant_price_segmentation_preserves_total() -> None:
    """Splitting a half-pay interval changes neither exact hours nor total cost."""
    split = build_paid_leave(
        schedule().policy.model_copy(update={"paid_accrual_limit_weeks": 2}),
        schedule().request,
    )
    whole = build_paid_leave(
        split.policy,
        split.request.model_copy(
            update={"split_on": ()},
        ),
    )
    assert_that(
        [(r.starts_on, r.ends_on) for r in split.rows] == [(START, MID), (MID, END)],
    )
    assert_that(len(whole.rows) == 1)
    left = price_paid_leave(prices(), selection(), split, choices(split))
    right = price_paid_leave(prices(), selection(), whole, choices(whole))
    assert_that(left.total == right.total == Fraction(63000, 73))


def test_base_inclusions_still_reject_an_added_allowance() -> None:
    """The bridge preserves the existing normal-pay double-counting guard."""
    leave = schedule()
    selected = choices(leave)
    first = selected[0].model_copy(
        update={
            "pricing": selected[0].pricing.model_copy(
                update={
                    "base_included_components": ("development",),
                },
            ),
            "allowances": (allowance(),),
        },
    )
    with pytest.raises(ValueError, match="included"):
        price_paid_leave(
            prices(quote(quote_id="development", component="development")),
            selection(),
            leave,
            (first, selected[1]),
        )


def test_choice_json_roundtrip_preserves_rational_exposure() -> None:
    """Strict JSON fractions survive nested request validation without coercion."""
    leave = schedule()
    selected = tuple(
        LeavePriceSelection.model_validate_json(c.model_dump_json())
        for c in choices(leave)
    )
    result = price_paid_leave(prices(), selection(), leave, selected)
    assert_that(result.total == Fraction(63000, 73))


def test_loading_cap_preserves_prior_consumption_and_partial_portion() -> None:
    """Only the remaining eligible hours receive the loading."""
    loaded = allocate_leave_loading_hours(
        (Fraction(38), Fraction(38), Fraction(38)),
        Fraction(152),
        Fraction(181, 2),
    )
    assert_that(loaded == (Fraction(38), Fraction(47, 2), Fraction(0)))
    with pytest.raises(ValueError, match="prior cap consumption"):
        allocate_leave_loading_hours((Fraction(38),), Fraction(152), Fraction(153))


def test_capped_loading_prices_separately_across_dated_quotes() -> None:
    """Compose reviewed loading-hour assumptions with dated leave prices."""
    leave = schedule()
    selected = choices(leave, second_quote="salary-new")
    release = dated_prices()
    loading_quotes = (
        quote(
            quote_id="loading-old",
            component="leave_loading",
            unit="hour",
            amount=Decimal("5.25"),
            ends_on=MID,
        ),
        quote(
            quote_id="loading-new",
            component="leave_loading",
            unit="hour",
            amount=Decimal(7),
            starts_on=MID,
        ),
    )
    release = release.model_copy(update={"quotes": (*release.quotes, *loading_quotes)})
    hours = allocate_leave_loading_hours(
        (Fraction(10), Fraction(10)),
        Fraction(20),
        Fraction(5),
    )
    with_loading = tuple(
        choice.model_copy(
            update={
                "allowances": (
                    allowance().model_copy(
                        update={
                            "quantity_id": price.quote_id,
                            "quote_id": price.quote_id,
                            "unit": "hour",
                            "quantity": quantity,
                            "valued_on": choice.starts_on,
                        },
                    ),
                ),
            },
        )
        for choice, price, quantity in zip(selected, loading_quotes, hours, strict=True)
    )
    result = price_paid_leave(release, selection(), leave, with_loading)
    assert_that(
        [row.pricing.pricing.rows[1].cost for row in result.rows]
        == [Fraction("52.5"), Fraction(35)],
    )
    assert_that(result.total == Fraction(73500, 73) + Fraction("87.5"))
    cap = LeaveLoadingMoneyCap(
        starts_on=date(2026, 1, 1),
        ends_on=date(2027, 1, 1),
        maximum=Decimal(80),
        prior_paid=Decimal(20),
        evidence="Synthetic reviewed cap",
    )
    accrued = tuple(
        choice.model_copy(update={"loading_accrued_on": cap.starts_on})
        for choice in with_loading
    )
    capped = price_paid_leave(release, selection(), leave, accrued, loading_cap=cap)
    with pytest.raises(ValueError, match="accrual date within"):
        price_paid_leave(release, selection(), leave, with_loading, loading_cap=cap)
    outside = accrued[1].model_copy(update={"loading_accrued_on": cap.ends_on})
    with pytest.raises(ValueError, match="accrual date within"):
        price_paid_leave(
            release,
            selection(),
            leave,
            (accrued[0], outside),
            loading_cap=cap,
        )
    assert_that(capped.loading_cap == cap)
    assert_that([row.loading_reduction for row in capped.rows] == [0, Fraction("27.5")])
    assert_that(capped.total == Fraction(73500, 73) + 60)
    with pytest.raises(ValueError, match="separately priced hourly"):
        price_paid_leave(release, selection(), leave, selected, loading_cap=cap)

    older = cap.model_copy(update={"ends_on": MID, "maximum": Decimal(50)})
    newer = cap.model_copy(
        update={"starts_on": MID, "maximum": Decimal(40), "prior_paid": Decimal(10)},
    )
    split = (
        accrued[0],
        accrued[1].model_copy(update={"loading_accrued_on": MID}),
    )
    dated = price_paid_leave(
        release,
        selection(),
        leave,
        split,
        loading_cap=(older, newer),
    )
    assert_that(dated.loading_caps == (older, newer))
    assert_that([row.loading_reduction for row in dated.rows] == [Fraction("22.5"), 5])
    assert_that(dated.total == Fraction(73500, 73) + 60)
    with pytest.raises(ValueError, match="nonoverlapping"):
        price_paid_leave(
            release,
            selection(),
            leave,
            split,
            loading_cap=(cap, newer),
        )


def test_loading_applies_hours_and_money_caps_independently() -> None:
    """A monetary cap can bind even while eligible hours remain."""
    hours = allocate_leave_loading_hours(
        (Fraction(10), Fraction(10), Fraction(5)),
        Fraction(20),
        Fraction(5),
    )
    rates = (Fraction("5.25"), Fraction(7), Fraction(8))
    result = price_leave_loading(hours, rates, Fraction(80), Fraction(20))
    assert_that(hours == (Fraction(10), Fraction(5), Fraction(0)))
    assert_that(result == (Fraction("52.50"), Fraction("7.50"), Fraction(0)))
    with pytest.raises(ValueError, match="prior payments"):
        price_leave_loading(hours, rates, Fraction(80), Fraction(81))


@pytest.mark.parametrize(("penalties", "expected"), [(0, 200), (200, 200), (250, 250)])
def test_cash_loading_selects_the_higher_amount(penalties: int, expected: int) -> None:
    """Compare two amounts from the same leave exposure without adding them."""
    result = select_leave_loading_alternative(
        Fraction(1000),
        Fraction("0.20"),
        Fraction(penalties),
    )
    assert_that(result.cash == expected and result.additional_days == 0)


def test_leave_election_replaces_cash_and_preserves_days() -> None:
    """A reviewed election needs no cash comparator, unlike the default route."""
    base, rate = Fraction(1000), Fraction("0.20")
    days = Fraction(4)
    result = select_leave_loading_alternative(base, rate, None, elected_days=days)
    assert_that(result.cash == 0 and result.additional_days == days)
    with pytest.raises(ValueError, match="reviewed forgone penalties"):
        select_leave_loading_alternative(base, rate, None)


def test_paid_leave_ledger_retains_cash_and_allocated_election() -> None:
    """Cash enters the row total while elected days remain a quantity."""
    leave = schedule()
    first, second = choices(leave, second_quote="salary-new")
    rate = Decimal("0.20")
    cash = LeaveLoadingComparison(
        rate=rate,
        forgone_penalties=Decimal(250),
        evidence="Reviewed synthetic roster",
    )
    election = LeaveLoadingComparison(
        rate=rate,
        elected_days=Decimal(4),
        evidence="Reviewed synthetic election allocated once",
    )
    result = price_paid_leave(
        dated_prices(),
        selection(),
        leave,
        (
            first.model_copy(update={"loading_comparison": cash}),
            second.model_copy(update={"loading_comparison": election}),
        ),
    )
    assert_that(result.total == Fraction(73500, 73) + 250)
    cash_result, election_result = (row.loading_alternative for row in result.rows)
    if cash_result is None or election_result is None:
        pytest.fail("Expected both loading decisions")
    assert_that(cash_result.cash == Fraction(250))
    assert_that(election_result.additional_days == Fraction(4))


def test_grouped_loading_compares_once_across_a_rate_change() -> None:
    """A pricing split does not select the higher cash basis twice."""
    leave = schedule()
    selected = choices(leave, second_quote="salary-new")
    grouped = tuple(
        row.model_copy(
            update={
                "loading_comparison": LeaveLoadingComparison(
                    rate=Decimal("0.20"),
                    forgone_penalties=Decimal(penalties),
                    evidence="Synthetic reviewed comparison period",
                    comparison_id="approved-leave",
                ),
            },
        )
        for row, penalties in zip(selected, (0, 190), strict=True)
    )
    result = price_paid_leave(dated_prices(), selection(), leave, grouped)
    base = Fraction(73500, 73)
    assert_that(result.total == base * Fraction(6, 5))
    assert_that(
        all(
            row.total == row.pricing.pricing.total * Fraction(6, 5)
            for row in result.rows
        ),
    )


@pytest.mark.parametrize(
    ("eligible", "base_only", "expected"),
    [
        ("15.2", "7.6", ("22.8", "15.2", "15.2")),
        ("30.4", "22.8", ("38", "15.2", "30.4")),
    ],
)
def test_combined_leave_cap_preserves_loading_allocation_range(
    eligible: str,
    base_only: str,
    expected: tuple[str, str, str],
) -> None:
    """The cap fixes total accrual while the loading basis may remain unresolved."""
    result = combined_leave_hours(Fraction(eligible), Fraction(base_only), Fraction(38))
    assert_that(
        (result.total, result.minimum_loaded, result.maximum_loaded)
        == tuple(map(Fraction, expected)),
    )


@pytest.mark.parametrize(
    ("worked", "required", "share", "expected"),
    [
        (3, 4, "1", "0"),
        (4, 4, "1", "2.92"),
        (8, 4, "1", "2.92"),
        (1, 1, "0.25", "0.73"),
    ],
)
def test_shift_credit_applies_once_per_qualifying_period(
    worked: int,
    required: int,
    share: str,
    expected: str,
) -> None:
    """Extra shifts do not generate additional credits within a period."""
    credit = qualifying_shift_leave_credit(
        worked, required, Fraction("2.92"), Fraction(share),
    )
    assert_that(credit == Fraction(expected))
