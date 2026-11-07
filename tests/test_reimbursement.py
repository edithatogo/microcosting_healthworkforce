# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Approved expense costs and remaining cap reconcile exactly."""

from datetime import date
from decimal import Decimal
from fractions import Fraction

import pytest
from pydantic import TypeAdapter

from src.reimbursement import (
    ReimbursementCarryDecision,
    ReimbursementClaim,
    ReimbursementLedger,
    ReimbursementPeriod,
    ReimbursementRecoveryDecision,
    build_reimbursement_ledger,
    cost_reimbursements,
    price_sa_residential_course_days,
    reimbursement_carry_amount,
    reimbursement_cost_after_recovery,
    sa_consultant_development_caps,
    sa_consultant_development_caps_2025,
    sa_ordinary_study_fee_amount,
    sa_residential_course_allowance,
    validate_vic_development_reimbursement,
    vic_specialist_cme_annual_cap,
)
from tests.checks import assert_that
from tests.test_unit_quotes import quantity, quote, release


def test_reimbursements_cost_only_approved_expenses_within_remaining_cap() -> None:
    """A partially used cap can limit one claim and exhaust the next."""
    start = date(2026, 7, 1)
    end = date(2027, 7, 1)
    claims = tuple(
        ReimbursementClaim(
            claim_id=f"claim-{index}",
            charged_on=start,
            eligible_amount=Decimal(amount),
            approval_evidence="Synthetic approved claim",
        )
        for index, amount in enumerate(("20.01", "70", "5"))
    )
    period = ReimbursementPeriod(
        currency="AUD",
        starts_on=start,
        ends_on=end,
        cap=Decimal("100.05"),
        prior_use=Decimal(25),
        applicability_evidence="Synthetic reviewed period",
        claims=claims,
    )
    rows = cost_reimbursements(period)
    assert_that([r.cost for r in rows] == [Fraction("20.01"), Fraction("55.04"), 0])
    assert_that([r.remaining for r in rows] == [Fraction("55.04"), 0, 0])
    assert_that(cost_reimbursements(period.model_copy(update={"claims": ()})) == ())
    for invalid in (
        (claims[0], claims[0]),
        (claims[0].model_copy(update={"charged_on": end}),),
    ):
        with pytest.raises(ValueError, match="Invalid reimbursement period"):
            cost_reimbursements(period.model_copy(update={"claims": invalid}))


def test_carry_uses_reviewed_balances_and_remaining_ceiling() -> None:
    """A renewed decision can admit the prior balance up to the ceiling."""
    decision = ReimbursementCarryDecision(
        current_remaining=Fraction(100, 3),
        prior_remaining=Decimal(40),
        carry_limit=Decimal(50),
        eligible_balances="current",
        decision_evidence="Synthetic reviewed allocation",
    )
    assert_that(reimbursement_carry_amount(decision) == Fraction(100, 3))
    renewed = decision.model_copy(update={"eligible_balances": "current_and_prior"})
    assert_that(reimbursement_carry_amount(renewed) == Fraction(50))
    expired = decision.model_copy(update={"eligible_balances": "none"})
    assert_that(reimbursement_carry_amount(expired) == 0)
    with pytest.raises(ValueError, match="carry_limit"):
        reimbursement_carry_amount(decision.model_copy(update={"carry_limit": -1}))


def test_exact_carry_can_fund_the_next_period() -> None:
    """A rational carry remains exact when used by a subsequent claim."""
    carry = reimbursement_carry_amount(
        ReimbursementCarryDecision(
            current_remaining=Fraction(100, 3),
            prior_remaining=Decimal(0),
            carry_limit=Decimal(50),
            eligible_balances="current",
            decision_evidence="Synthetic year-end review",
        ),
    )
    day = date(2027, 7, 1)
    claim = ReimbursementClaim(
        claim_id="next-year",
        charged_on=day,
        eligible_amount=Decimal(150),
        approval_evidence="Synthetic approved expense",
    )
    period = ReimbursementPeriod(
        currency="AUD",
        starts_on=day,
        ends_on=date(2028, 7, 1),
        cap=100 + carry,
        prior_use=Fraction(1, 3),
        applicability_evidence="Synthetic reviewed cap including carry",
        claims=(claim,),
    )
    (row,) = cost_reimbursements(period)
    assert_that(row.cost == Fraction(133))
    assert_that(row.remaining == 0)


def test_sa_consultant_development_caps_at_half_day_boundary() -> None:
    """The lower bracket ends at exactly five nominal half-days."""
    assert_that(
        sa_consultant_development_caps(Decimal("4.99"))
        == (Fraction(11000), Fraction(22000)),
    )
    assert_that(
        sa_consultant_development_caps(Decimal(5))
        == (Fraction(22000), Fraction(44000)),
    )
    with pytest.raises(ValueError, match="positive nominal half-days"):
        sa_consultant_development_caps(Decimal(0))


def test_sa_development_claim_respects_reviewed_two_year_headroom() -> None:
    """The annual allocation and carry together fit the two-year ceiling."""
    annual_cap, two_year_cap = sa_consultant_development_caps(Decimal(5))
    carry = reimbursement_carry_amount(
        ReimbursementCarryDecision(
            current_remaining=Decimal(18000),
            prior_remaining=Decimal(9000),
            carry_limit=two_year_cap - annual_cap,
            eligible_balances="current_and_prior",
            decision_evidence="Synthetic reviewed eligible balances",
        ),
    )
    start = date(2023, 7, 1)
    (row,) = cost_reimbursements(
        ReimbursementPeriod(
            currency="AUD",
            starts_on=start,
            ends_on=date(2024, 7, 1),
            cap=annual_cap + carry,
            prior_use=Decimal("1500.25"),
            applicability_evidence="Synthetic reviewed cap and carry allocation",
            claims=(
                ReimbursementClaim(
                    claim_id="approved-development-expense",
                    charged_on=start,
                    eligible_amount=Decimal(43000),
                    approval_evidence="Synthetic FBT-inclusive approved amount",
                ),
            ),
        ),
    )
    assert_that(carry == Fraction(22000))
    assert_that(row.cost == Fraction("42499.75"))
    assert_that(row.remaining == 0)


def test_sa_successor_development_cap_effective_dates() -> None:
    """The successor raises both brackets at its operative date."""
    select = sa_consultant_development_caps_2025
    with pytest.raises(ValueError, match="precedes"):
        select(Decimal(5), date(2025, 4, 13))
    for day in (date(2025, 4, 14), date(2026, 4, 13)):
        assert_that(select(Decimal(5), day) == (22000, 44000))
    boundary = date(2026, 4, 14)
    assert_that(select(Decimal(5), boundary) == (23000, 46000))
    assert_that(select(Decimal("4.99"), boundary) == (11500, 23000))


def test_reimbursement_recovery_is_discretionary_and_limited_to_excess() -> None:
    """An employer can choose a smaller recovery than the eligible excess."""
    decision = ReimbursementRecoveryDecision(
        reimbursed=Decimal("14000.25"),
        prorated_entitlement=Decimal(11000),
        approved_recovery=Decimal("2500.10"),
        decision_evidence="Synthetic approved resignation reconciliation",
    )
    assert_that(reimbursement_cost_after_recovery(decision) == Fraction("11500.15"))
    declined = decision.model_copy(update={"approved_recovery": Decimal(0)})
    assert_that(reimbursement_cost_after_recovery(declined) == Fraction("14000.25"))
    excess = decision.model_copy(update={"approved_recovery": Decimal("3000.26")})
    with pytest.raises(ValueError, match="exceeds reimbursement"):
        reimbursement_cost_after_recovery(excess)


def test_reviewed_uncapped_claims_cost_only_eligible_expenses() -> None:
    """An uncapped period has no balance and creates no standing allowance."""
    start = date(2022, 7, 1)
    period = ReimbursementPeriod(
        currency="AUD",
        starts_on=start,
        ends_on=date(2023, 7, 1),
        cap=None,
        prior_use=Decimal(0),
        applicability_evidence="Synthetic covered program and uncapped clause",
        claims=(),
    )
    assert_that(cost_reimbursements(period) == ())
    claim = ReimbursementClaim(
        claim_id="development-expense",
        charged_on=start,
        eligible_amount=Decimal("625.45"),
        approval_evidence="Synthetic proof of reasonable expense",
    )
    reviewed = ReimbursementPeriod.model_validate_json(
        period.model_copy(update={"claims": (claim,)}).model_dump_json(),
    )
    ledger = build_reimbursement_ledger(reviewed)
    adapter = TypeAdapter(ReimbursementLedger)
    assert_that(adapter.validate_json(adapter.dump_json(ledger)) == ledger)
    assert_that(ledger.period == reviewed)
    assert_that(ledger.total == Fraction("625.45"))
    (row,) = ledger.rows
    assert_that(row.cost == Fraction("625.45"))
    assert_that(row.remaining is None)
    with pytest.raises(ValueError, match="Invalid reimbursement period"):
        cost_reimbursements(period.model_copy(update={"prior_use": Decimal(1)}))


def test_sa_ordinary_study_fees_require_proof_of_passing() -> None:
    """Only proven compulsory tuition and examination fees price here."""
    price = sa_ordinary_study_fee_amount
    tuition, exams = Decimal("675.25"), Fraction(1, 3)
    assert_that(
        price(tuition, exams, proof_of_passing=True) == Fraction("675.25") + exams,
    )
    assert_that(price(tuition, exams, proof_of_passing=False) == 0)
    with pytest.raises(ValueError, match="nonnegative"):
        price(Decimal(-1), exams, proof_of_passing=True)


def test_proven_study_fees_enter_claim_ledger_without_rounding() -> None:
    """The exact fee result can be used directly in a serialized claim."""
    amount = sa_ordinary_study_fee_amount(
        Decimal("600.25"),
        Fraction(1, 3),
        proof_of_passing=True,
    )
    start = date(2022, 7, 1)
    period = ReimbursementPeriod(
        currency="AUD",
        starts_on=start,
        ends_on=date(2023, 7, 1),
        cap=None,
        prior_use=Decimal(0),
        applicability_evidence="Synthetic reviewed ordinary study fee route",
        claims=(
            ReimbursementClaim(
                claim_id="study-fees",
                charged_on=start,
                eligible_amount=amount,
                approval_evidence="Synthetic proof of passing and fee evidence",
            ),
        ),
    )
    ledger = build_reimbursement_ledger(
        ReimbursementPeriod.model_validate_json(period.model_dump_json()),
    )
    assert_that(ledger.total == Fraction("600.25") + Fraction(1, 3))


def test_sa_residential_course_allowance_uses_programme_duration() -> None:
    """Two weeks uses the short rate and the next day uses the long rate."""
    rates = {
        "short_course_daily_rate": Fraction("13.60"),
        "long_course_daily_rate": Fraction("28.80"),
    }
    assert_that(sa_residential_course_allowance(14, 10, **rates) == Fraction(136))
    assert_that(sa_residential_course_allowance(15, 10, **rates) == Fraction(288))
    assert_that(sa_residential_course_allowance(15, 0, **rates) == Fraction(0))
    with pytest.raises(ValueError, match="programme duration"):
        sa_residential_course_allowance(14, 15, **rates)


def test_sa_residential_course_days_keep_dated_quotes_and_enforce_band() -> None:
    """Select dated short-course quotes and reject the same dates for a long course."""
    rates = release(
        quote(
            quote_id="early",
            component="residential_course_short",
            unit="course_day",
            amount=Decimal("13.60"),
            ends_on=date(2026, 2, 1),
        ),
        quote(
            quote_id="later",
            component="residential_course_short",
            unit="course_day",
            amount=Decimal("14.10"),
            starts_on=date(2026, 2, 1),
        ),
    )
    early = quantity(quote_id="early", unit="course_day", valued_on=date(2026, 1, 31))
    later = quantity(quantity_id="event-2", quote_id="later", unit="course_day")
    starts_on = date(2026, 1, 30)
    ends_on = date(2026, 2, 13)
    result = price_sa_residential_course_days(
        rates,
        (early, later),
        starts_on=starts_on,
        ends_on=ends_on,
    )
    assert_that(result.total == Fraction("27.70"))
    assert_that([row.quote.quote_id for row in result.rows] == ["early", "later"])
    with pytest.raises(ValueError, match="duration band"):
        price_sa_residential_course_days(
            rates,
            (early, later),
            starts_on=starts_on,
            ends_on=date(2026, 2, 14),
        )
    with pytest.raises(ValueError, match="distinct date"):
        price_sa_residential_course_days(
            rates,
            (early, early),
            starts_on=starts_on,
            ends_on=ends_on,
        )
    with pytest.raises(ValueError, match="outside the reviewed programme"):
        price_sa_residential_course_days(
            rates,
            (early, later),
            starts_on=starts_on,
            ends_on=date(2026, 2, 1),
        )


@pytest.mark.parametrize(
    ("applied_on", "receipt", "error"),
    [
        (date(2023, 1, 15), "Reviewed official receipt", None),
        (date(2023, 1, 16), "Reviewed official receipt", "within 14 days"),
        (date(2022, 12, 31), "Reviewed official receipt", "within 14 days"),
        (date(2023, 1, 15), " ", "receipt evidence"),
    ],
)
def test_vic_development_reimbursement_filing(
    applied_on: date,
    receipt: str,
    error: str | None,
) -> None:
    """Preserve the approved amount and check filing and receipt evidence."""
    claim = ReimbursementClaim(
        claim_id="development",
        charged_on=date(2023, 2, 1),
        eligible_amount=Fraction("75.25"),
        approval_evidence="Synthetic partial approval",
    )
    arguments = {
        "returned_on": date(2023, 1, 1),
        "applied_on": applied_on,
    }
    if error is None:
        approved = validate_vic_development_reimbursement(
            claim,
            receipt_evidence=receipt,
            **arguments,
        )
        assert_that(approved == claim)
        period = ReimbursementPeriod(
            currency="AUD",
            starts_on=date(2023, 2, 1),
            ends_on=date(2023, 3, 1),
            cap=None,
            prior_use=Decimal(0),
            applicability_evidence="Synthetic reviewed Victorian clause 75 coverage",
            claims=(approved,),
        )
        ledger = build_reimbursement_ledger(period)
        assert_that(len(ledger.rows) == 1)
        assert_that(ledger.total == Fraction("75.25"))
    else:
        with pytest.raises(ValueError, match=error):
            validate_vic_development_reimbursement(
                claim,
                receipt_evidence=receipt,
                **arguments,
            )


def test_vic_specialist_cme_cap_requires_reviewed_column() -> None:
    """An actual payroll date cannot implicitly select a published column."""
    assert_that(vic_specialist_cme_annual_cap(date(2022, 3, 1)) == Fraction("29000.16"))
    assert_that(vic_specialist_cme_annual_cap(date(2023, 9, 1)) == Fraction("29725.16"))
    assert_that(vic_specialist_cme_annual_cap(date(2025, 3, 1)) == Fraction("30468.29"))
    with pytest.raises(ValueError, match="published Victorian specialist CME"):
        vic_specialist_cme_annual_cap(date(2025, 3, 3))


def test_vic_specialist_cme_cap_limits_approved_claims() -> None:
    """The published ceiling limits expenditure after prior use."""
    cap = vic_specialist_cme_annual_cap(date(2022, 3, 1))
    period = ReimbursementPeriod(
        currency="AUD",
        starts_on=date(2023, 1, 1),
        ends_on=date(2024, 1, 1),
        cap=cap,
        prior_use=Fraction("28000.10"),
        applicability_evidence="Synthetic reviewed full cap and accounting period",
        claims=(
            ReimbursementClaim(
                claim_id="synthetic-cme",
                charged_on=date(2023, 2, 1),
                eligible_amount=Fraction("1100.25"),
                approval_evidence="Synthetic approved expense",
            ),
        ),
    )
    ledger = build_reimbursement_ledger(period)
    assert_that(ledger.total == Fraction("1000.06"))
    assert_that(ledger.rows[0].remaining == 0)
    assert_that(
        build_reimbursement_ledger(period.model_copy(update={"claims": ()})).total == 0,
    )
