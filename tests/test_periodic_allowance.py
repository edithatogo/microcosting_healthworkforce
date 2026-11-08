# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Test explicit periodic allowance calculation without inferring eligibility."""

from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from fractions import Fraction

import pytest

from src.condition_history import release_sha256
from src.conditions import ConditionRelease
from src.period_contributions import (
    ContributionPayment,
    cost_contribution_payments,
    reconcile_allowance_payment,
)
from src.periodic_allowance import (
    AllowancePeriod,
    AllowancePortion,
    cost_periodic_allowance,
    cost_periodic_allowance_across_releases,
    cost_periodic_allowance_schedule,
)
from src.source_registry import SourceRegistry
from tests.checks import assert_that
from tests.test_conditions import condition
from tests.test_period_contributions import START, prices, rule
from tests.test_period_contributions import period as contribution_period
from tests.test_source_registry import source


def release() -> ConditionRelease:
    """Use a synthetic accepted annual amount and independently scoped source."""
    return ConditionRelease(
        release_id="synthetic",
        jurisdiction="QLD",
        employer="Synthetic employer",
        classification="Synthetic grade",
        sources=SourceRegistry(records=(source(),)),
        conditions=(condition("training", "fixed_annual", "1975", "AUD/year"),),
    )


def portion(label: str, hours: str, accrual: str, payment: str) -> AllowancePortion:
    """Create an explicitly reviewed test allocation."""
    return AllowancePortion(
        label=label,
        hours=Decimal(hours),
        accrual_factor=Decimal(accrual),
        payment_factor=Decimal(payment),
    )


def period(*portions: AllowancePortion) -> AllowancePeriod:
    """Use a caller-supplied 76-hour period and 26 periods per year."""
    return AllowancePeriod(
        starts_on=date(2026, 6, 1),
        ends_on=date(2026, 6, 15),
        full_time_hours=Decimal(76),
        periods_per_year=Decimal(26),
        portions=portions,
    )


def test_part_time_and_distinct_half_pay_accrual() -> None:
    """Prorate exact dollars and keep accrual separate from cash payment."""
    ordinary = portion("ordinary", "30.4", "1", "1")
    result = cost_periodic_allowance(release(), "training", period(ordinary))
    assert_that(result.payable == result.accrued == Fraction(395, 13))
    assert_that(result.condition.condition_id == "training")
    leave = portion("half-pay", "30.4", "1", "0.5")
    separate = cost_periodic_allowance(release(), "training", period(leave))
    assert_that(separate.accrued == Fraction(395, 13))
    assert_that(separate.payable == Fraction(395, 26))


def test_unpaid_and_overtime_depend_on_explicit_inputs() -> None:
    """Zero factors contribute nothing; no leave or overtime rules are inferred."""
    result = cost_periodic_allowance(
        release(),
        "training",
        period(portion("unpaid", "20", "0", "0")),
    )
    assert_that(result.accrued == result.payable == 0)


def test_invalid_or_changing_period_is_rejected() -> None:
    """Reject unsupported period scope and malformed copied allocations."""
    valid = period(portion("ordinary", "30", "1", "1"))
    crossed = valid.model_copy(update={"ends_on": date(2027, 1, 2)})
    with pytest.raises(ValueError, match="whole period"):
        cost_periodic_allowance(release(), "training", crossed)
    with pytest.raises(ValueError, match="whole period"):
        cost_periodic_allowance(release(), "missing", valid)
    excessive = valid.model_copy(update={"full_time_hours": Decimal(10)})
    with pytest.raises(ValueError, match="exceed"):
        cost_periodic_allowance(release(), "training", excessive)
    with pytest.raises(ValueError, match="unique"):
        period(portion("same", "1", "1", "1"), portion("same", "1", "1", "1"))


@pytest.mark.parametrize(
    ("boundary", "old_amount", "new_amount"),
    [
        (date(2026, 6, 8), "1975", "3950"),
        (date(2026, 7, 1), "23395", "24097"),
        (date(2026, 7, 1), "28408", "29260"),
    ],
)
def test_split_period_retains_nominal_denominator_and_condition_lineage(
    boundary: date,
    old_amount: str,
    new_amount: str,
) -> None:
    """A mid-period rate change is split without charging a full period twice."""
    first = condition("first", "fixed_annual", old_amount, "AUD/year").model_copy(
        update={"component": "training", "effective_to": boundary},
    )
    second = condition("second", "fixed_annual", new_amount, "AUD/year").model_copy(
        update={"component": "training", "effective_from": boundary},
    )
    dated = release().model_copy(update={"conditions": (first, second)})
    first_half = period(portion("first-half", "38", "1", "1")).model_copy(
        update={"starts_on": boundary - timedelta(days=7), "ends_on": boundary},
    )
    second_half = period(portion("second-half", "38", "1", "1")).model_copy(
        update={"starts_on": boundary, "ends_on": boundary + timedelta(days=7)},
    )
    before = cost_periodic_allowance(dated, "training", first_half)
    after = cost_periodic_allowance(dated, "training", second_half)
    assert_that(
        before.payable + after.payable
        == (Fraction(old_amount) + Fraction(new_amount)) / 52,
    )
    assert_that(before.condition.condition_id == "first")
    assert_that(after.condition.condition_id == "second")
    assert_that(before.release_sha256 == after.release_sha256)
    assert_that(before.release_sha256 == release_sha256(dated))
    unsplit = period(portion("whole", "76", "1", "1")).model_copy(
        update={"starts_on": first_half.starts_on, "ends_on": second_half.ends_on},
    )
    with pytest.raises(ValueError, match="cover the whole period"):
        cost_periodic_allowance(dated, "training", unsplit)
    scheduled = cost_periodic_allowance_schedule(
        dated,
        "training",
        unsplit.model_copy(
            update={"portions": first_half.portions + second_half.portions},
        ),
        (first_half, second_half),
    )
    assert_that(scheduled.segments == (before, after))
    assert_that(scheduled.payable == before.payable + after.payable)


@pytest.mark.parametrize("payment_factor", ["1", "0.5"])
def test_schedule_conserves_hours_across_rate_change(payment_factor: str) -> None:
    """Price the same nominal period once across two explicitly allocated rates."""
    first = condition("first", "fixed_annual", "1975", "AUD/year").model_copy(
        update={"component": "training", "effective_to": date(2026, 6, 8)},
    )
    second = condition("second", "fixed_annual", "3950", "AUD/year").model_copy(
        update={"component": "training", "effective_from": date(2026, 6, 8)},
    )
    dated = release().model_copy(update={"conditions": (first, second)})
    parent = period(portion("ordinary", "76", "1", payment_factor))
    segments = (
        period(portion("ordinary", "38", "1", payment_factor)).model_copy(
            update={"ends_on": date(2026, 6, 8)},
        ),
        period(portion("ordinary", "38", "1", payment_factor)).model_copy(
            update={"starts_on": date(2026, 6, 8)},
        ),
    )
    result = cost_periodic_allowance_schedule(dated, "training", parent, segments)
    assert_that(result.accrued == Fraction(5925, 52))
    assert_that(result.payable == result.accrued * Fraction(payment_factor))
    assert_that(
        [c.condition.condition_id for c in result.segments] == ["first", "second"],
    )
    assert_that(result.segments[0].release_sha256 == result.segments[1].release_sha256)


def test_schedule_rejects_duplicate_hours_and_changed_factors() -> None:
    """Contiguous dates cannot hide repeated allocations or altered leave factors."""
    parent = period(portion("ordinary", "38", "1", "1"))
    before = parent.model_copy(update={"ends_on": date(2026, 6, 8)})
    after = parent.model_copy(update={"starts_on": date(2026, 6, 8)})
    with pytest.raises(ValueError, match="conserve"):
        cost_periodic_allowance_schedule(release(), "training", parent, (before, after))
    altered = period(portion("ordinary", "38", "1", "0.5"))
    with pytest.raises(ValueError, match="conserve"):
        cost_periodic_allowance_schedule(release(), "training", parent, (altered,))


def test_schedule_rejects_gaps_overlaps_and_changed_denominators() -> None:
    """Every segment belongs to one complete declared payroll period."""
    parent = period(portion("ordinary", "38", "1", "1"))
    with pytest.raises(ValueError, match="at least one"):
        cost_periodic_allowance_schedule(release(), "training", parent, ())
    for invalid in (
        parent.model_copy(update={"starts_on": date(2026, 6, 2)}),
        parent.model_copy(update={"ends_on": date(2026, 6, 14)}),
    ):
        with pytest.raises(ValueError, match="contiguously"):
            cost_periodic_allowance_schedule(release(), "training", parent, (invalid,))
    with pytest.raises(ValueError, match="contiguously"):
        cost_periodic_allowance_schedule(
            release(),
            "training",
            parent,
            (parent, parent),
        )
    bound = parent.model_copy(
        update={"resource_id": "staff", "allocation_id": "worker"},
    )
    assert_that(
        cost_periodic_allowance_schedule(release(), "training", bound, (bound,))
        .segments[0]
        .period.allocation_id
        == "worker",
    )
    with pytest.raises(ValueError, match="retain the parent assignment"):
        cost_periodic_allowance_schedule(release(), "training", bound, (parent,))
    changed = parent.model_copy(update={"periods_per_year": Decimal(27)})
    with pytest.raises(ValueError, match="denominators"):
        cost_periodic_allowance_schedule(release(), "training", parent, (changed,))


def test_transfer_prices_each_release_and_conserves_hours() -> None:
    """A transfer retains both releases while sharing one payroll denominator."""
    first = release()
    second = first.model_copy(
        update={
            "release_id": "second-release",
            "conditions": (condition("training", "fixed_annual", "3950", "AUD/year"),),
        },
    )
    boundary = date(2026, 6, 8)
    parent = period(portion("ordinary", "76", "1", "1"))
    half = period(portion("ordinary", "38", "1", "1"))
    before = half.model_copy(update={"ends_on": boundary})
    after = half.model_copy(update={"starts_on": boundary})
    result = cost_periodic_allowance_across_releases(
        "training",
        parent,
        ((first, before), (second, after)),
    )
    assert_that(result.payable == Fraction(5925, 52))
    assert_that(
        [item.release_sha256 for item in result.segments]
        == [release_sha256(first), release_sha256(second)],
    )
    with pytest.raises(ValueError, match="conserve"):
        cost_periodic_allowance_across_releases(
            "training",
            parent,
            (
                (first, before),
                (
                    second,
                    after.model_copy(
                        update={"portions": (portion("ordinary", "37", "1", "1"),)},
                    ),
                ),
            ),
        )


def test_periodic_allowance_rejects_component_in_salary_bundle() -> None:
    """Identify the bundled route before attempting a separate allowance price."""
    base = release()
    salary = condition("salary", "salary", "100000", "AUD/year")
    bundled = salary.model_copy(update={"included_components": ("training",)})
    reviewed = ConditionRelease.model_validate(
        {**base.model_dump(), "conditions": (bundled,)},
    )
    with pytest.raises(ValueError, match="duplicates a salary inclusion"):
        cost_periodic_allowance(
            reviewed,
            "training",
            period(portion("ordinary", "76", "1", "1")),
        )


def test_vehicle_allowance_prorates_mixed_leave_in_one_fortnight() -> None:
    """Price full-pay, half-pay and unpaid portions of a part-time period."""
    result = cost_periodic_allowance(
        release(),
        "training",
        period(
            portion("full-pay", "19", "1", "1"),
            portion("half-pay", "19", "0.5", "0.5"),
            portion("unpaid", "19", "0", "0"),
        ),
    )
    assert_that(result.payable == result.accrued == Fraction(5925, 208))


def test_reconcile_actual_posting_against_payable_allowance() -> None:
    """Retain the posting and exact difference independently of accrual."""
    allowance = cost_periodic_allowance(
        release(),
        "training",
        period(portion("half-pay", "19", "1", "0.5")).model_copy(
            update={"starts_on": START.date(), "ends_on": date(2026, 1, 15)},
        ),
    )
    payment = ContributionPayment(
        payment_id="posting",
        resource_id="staff",
        allocation_id="worker",
        component="training",
        paid_at=START,
        amount=Decimal("9.50"),
        evidence="Synthetic payroll posting",
    )
    bound_period = allowance.period.model_copy(
        update={"resource_id": "staff", "allocation_id": "worker"},
    )
    bound = replace(allowance, period=bound_period)
    assert_that(reconcile_allowance_payment(bound, payment).payment == payment)
    with pytest.raises(ValueError, match="priced allowance assignment"):
        reconcile_allowance_payment(
            bound,
            payment.model_copy(update={"allocation_id": "different-worker"}),
        )
    late = payment.model_copy(
        update={
            "earned_from": allowance.period.starts_on,
            "earned_to": allowance.period.ends_on,
            "paid_at": START + timedelta(days=30),
        },
    )
    assert_that(reconcile_allowance_payment(allowance, late).payment == late)
    with pytest.raises(ValueError, match="earning interval does not match"):
        reconcile_allowance_payment(
            allowance,
            late.model_copy(update={"earned_to": date(2026, 1, 16)}),
        )
    result = reconcile_allowance_payment(allowance, payment)
    assert_that(result.allowance == allowance and result.payment == payment)
    assert_that(result.paid_minus_payable == Fraction("9.50") - allowance.payable)
    assert_that(allowance.payable != allowance.accrued)
    original = rule()
    basis = original.alternatives[0].model_copy(update={"bases": ("training",)})
    policy = original.model_copy(update={"alternatives": (basis,)})
    priced = cost_contribution_payments(
        prices(),
        contribution_period(),
        policy,
        (),
        allowance_reconciliations=(result,),
    )
    assert_that(priced.contribution == Fraction("0.95"))
    assert_that(priced.allowance_reconciliations == (result,))
    excluded = cost_contribution_payments(
        prices(),
        contribution_period(),
        original,
        (),
        allowance_reconciliations=(result,),
    )
    assert_that(excluded.contribution == Fraction(0))
    assert_that(excluded.allowance_reconciliations == (result,))
    inclusive = basis.model_copy(
        update={"alternative_id": "inclusive", "bases": ("salary", "training")},
    )
    comparison = original.model_copy(
        update={"alternatives": (original.alternatives[0], inclusive)},
    )
    salary = payment.model_copy(
        update={"payment_id": "salary", "component": "salary", "amount": Decimal(100)},
    )
    compared = cost_contribution_payments(
        prices(),
        contribution_period(),
        comparison,
        (salary,),
        allowance_reconciliations=(result,),
    )
    assert_that(compared.contribution == Fraction("10.95"))
    totals = {item.amount for item in compared.alternatives}
    assert_that(totals == {10, Fraction("10.95")})
    with pytest.raises(ValueError, match="Duplicate contribution payment"):
        cost_contribution_payments(
            prices(),
            contribution_period(),
            policy,
            (payment,),
            allowance_reconciliations=(result,),
        )
    with pytest.raises(ValueError, match="component does not match"):
        reconcile_allowance_payment(
            allowance,
            payment.model_copy(update={"component": "other"}),
        )
    with pytest.raises(ValueError, match="evidence must be nonblank"):
        reconcile_allowance_payment(
            allowance,
            payment.model_copy(update={"evidence": " "}),
        )
    wrong_scope = replace(
        result,
        allowance=replace(
            allowance,
            scope=("QLD", "Other employer", "Synthetic grade"),
        ),
    )
    with pytest.raises(ValueError, match="differs from payroll"):
        cost_contribution_payments(
            prices(),
            contribution_period(),
            policy,
            (),
            allowance_reconciliations=(wrong_scope,),
        )
