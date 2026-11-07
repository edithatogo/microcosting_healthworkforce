# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Whole-period alternative comparisons preserve distinct bases and exact totals."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, localcontext
from fractions import Fraction

import pytest

from src.costing import Activity, CostRelease, ResourceUse
from src.period_contributions import (
    ContributionAlternative,
    ContributionCap,
    ContributionFactor,
    ContributionPayment,
    ContributionPeriod,
    ContributionRule,
    cost_contribution_activities,
    cost_contribution_payments,
    cost_contribution_snapshot,
)
from tests.checks import assert_that
from tests.test_costing import release

START = datetime(2026, 1, 1, 11, tzinfo=UTC)
END = START + timedelta(hours=2)


def prices() -> CostRelease:
    """Salary100 both hours; explicit supplement100 then zero at noon."""
    original = release()
    return CostRelease.model_validate(
        {
            **original.model_dump(),
            "rates": (
                original.rates[0].model_copy(
                    update={
                        "components": {
                            "salary": Decimal(100),
                            "supplement": Decimal(100),
                        },
                    },
                ),
                original.rates[1].model_copy(
                    update={
                        "components": {
                            "salary": Decimal(100),
                            "supplement": Decimal(0),
                        },
                    },
                ),
            ),
        },
    )


def factor(
    identity: str,
    value: str,
    start: datetime = START,
    end: datetime = END,
) -> ContributionFactor:
    """Declare a synthetic reviewed fraction and its exact operative interval."""
    return ContributionFactor(
        factor_id=identity,
        fraction=Decimal(value),
        starts_at=start,
        ends_at=end,
        source_id="synthetic-award-1",
        source_sha256="a" * 64,
        citation="Synthetic factor clause",
        reviewed=True,
    )


def rule() -> ContributionRule:
    """Compare10% of salary+supplement with15% of salary, once over the period."""
    return ContributionRule(
        rule_id="synthetic-comparison",
        component="contribution",
        alternatives=(
            ContributionAlternative(
                alternative_id="broad",
                bases=("salary", "supplement"),
                factors=(factor("broad-1", "0.1"),),
            ),
            ContributionAlternative(
                alternative_id="narrow",
                bases=("salary",),
                factors=(factor("narrow-1", "0.15"),),
            ),
        ),
        source_id="synthetic-award-1",
        source_sha256="a" * 64,
        citation="Synthetic comparison clause",
        effective_from=date(2026, 1, 1),
        effective_to=date(2027, 1, 1),
        reviewed=True,
        local_timezone="UTC",
    )


def period() -> ContributionPeriod:
    """Declare one worker period with all relevant earnings supplied."""
    return ContributionPeriod(
        period_id="declared",
        resource_id="staff",
        allocation_id="worker",
        starts_at=START,
        ends_at=END,
        earnings_complete=True,
    )


def activity() -> Activity:
    """Use actual elapsed time for one identified resource."""
    return Activity(
        activity_id="work",
        resource_id="staff",
        allocation_id="worker",
        starts_at=START,
        ends_at=END,
        resources=Decimal(1),
    )


def test_greater_of_period_totals_is_not_sum_of_segment_maxima() -> None:
    """20+10 versus15+15 tie30; choosing each segment's winner would overcharge35."""
    result = cost_contribution_activities(prices(), period(), rule(), (activity(),))
    assert_that(
        {a.alternative_id: a.amount for a in result.alternatives}
        == {"broad": Fraction(30), "narrow": Fraction(30)},
    )
    assert_that(result.winning_alternative_ids == ("broad", "narrow"))
    assert_that(
        result.contribution == Fraction(30) and result.exact_total == Fraction(330),
    )
    assert_that(result.base.total == Decimal(300))
    assert_that(
        [r.amount for r in result.rows if r.alternative_id == "broad"]
        == [Fraction(20), Fraction(10)],
    )


def test_single_period_contribution_basis() -> None:
    """Price a single contribution basis across effective-dated segments."""
    original = rule()
    single = original.model_copy(update={"alternatives": (original.alternatives[0],)})
    result = cost_contribution_activities(prices(), period(), single, (activity(),))
    assert_that(result.winning_alternative_ids == ("broad",))
    assert_that(result.contribution == Fraction(30))
    assert_that(result.exact_total == Fraction(330))


def test_segmentation_order_and_alternative_order_preserve_money() -> None:
    """Splitting at an arbitrary minute cannot reset the comparison period."""
    whole = cost_contribution_activities(prices(), period(), rule(), (activity(),))
    a = activity()
    boundary = START + timedelta(minutes=37)
    pieces = (
        a.model_copy(update={"activity_id": "late", "starts_at": boundary}),
        a.model_copy(update={"activity_id": "early", "ends_at": boundary}),
    )
    reversed_rule = rule().model_copy(
        update={"alternatives": tuple(reversed(rule().alternatives))},
    )
    split = cost_contribution_activities(prices(), period(), reversed_rule, pieces)
    assert_that(whole.exact_total == split.exact_total == Fraction(330))
    assert_that(whole.contribution == split.contribution == Fraction(30))
    assert_that(whole.winning_alternative_ids == split.winning_alternative_ids)


def test_factor_change_and_wage_change_are_split_before_comparing_totals() -> None:
    """Broad20+20 beats narrow30; the second fraction applies only after noon."""
    original = rule()
    broad = original.alternatives[0].model_copy(
        update={
            "factors": (
                factor("first", "0.1", START, START + timedelta(hours=1)),
                factor("last", "0.2", START + timedelta(hours=1), END),
            ),
        },
    )
    changed = original.model_copy(
        update={"alternatives": (broad, original.alternatives[1])},
    )
    result = cost_contribution_activities(prices(), period(), changed, (activity(),))
    assert_that(
        result.contribution == Fraction(40) and result.exact_total == Fraction(340),
    )
    assert_that(result.winning_alternative_ids == ("broad",))
    assert_that(
        {r.factor.factor_id for r in result.rows if r.alternative_id == "broad"}
        == {"first", "last"},
    )
    with pytest.raises(ValueError, match="single factor"):
        cost_contribution_snapshot(
            prices(),
            period(),
            changed,
            START,
            ResourceUse(resource_id="staff", hours=Decimal(2)),
        )


@pytest.mark.parametrize("basis_count", [1, 2])
def test_static_and_dynamic_agree_for_constant_prices_and_factors(
    basis_count: int,
) -> None:
    """At a stationary200/hour, broad40 beats narrow30; total440."""
    original = prices()
    constant = original.model_copy(
        update={"rates": (original.rates[0].model_copy(update={"ends_at": None}),)},
    )
    policy = rule()
    policy = policy.model_copy(
        update={"alternatives": policy.alternatives[:basis_count]},
    )
    static = cost_contribution_snapshot(
        constant,
        period(),
        policy,
        START,
        ResourceUse(resource_id="staff", hours=Decimal(2)),
    )
    dynamic = cost_contribution_activities(constant, period(), policy, (activity(),))
    assert_that(static.contribution == dynamic.contribution == Fraction(40))
    assert_that(static.exact_total == dynamic.exact_total == Fraction(440))
    assert_that(
        static.mode == "static_assumed_quantity"
        and dynamic.mode == "dynamic_earned_activities",
    )


def test_explicit_zero_earnings_retains_tied_alternatives() -> None:
    """A complete zero-earning period is zero; missing coverage still fails."""
    result = cost_contribution_activities(prices(), period(), rule(), ())
    assert_that(result.exact_total == result.contribution == 0)
    assert_that(result.winning_alternative_ids == ("broad", "narrow"))
    bad = rule()
    bad = bad.model_copy(
        update={
            "alternatives": (
                bad.alternatives[0].model_copy(update={"bases": ("unknown",)}),
                bad.alternatives[1],
            ),
        },
    )
    with pytest.raises(ValueError, match="base"):
        cost_contribution_activities(prices(), period(), bad, ())


def test_incomplete_period_wrong_worker_and_aggregate_resources_fail() -> None:
    """No missing earning history, mixed employee or aggregate headcount default."""
    with pytest.raises(ValueError, match="Complete relevant period earnings"):
        cost_contribution_activities(
            prices(),
            period().model_copy(update={"earnings_complete": False}),
            rule(),
            (activity(),),
        )
    for bad in [
        activity().model_copy(update={"allocation_id": "other"}),
        activity().model_copy(update={"resources": Decimal(2)}),
        activity().model_copy(update={"ends_at": END + timedelta(seconds=1)}),
    ]:
        with pytest.raises(ValueError, match=r"allocation|resource|period"):
            cost_contribution_activities(prices(), period(), rule(), (bad,))


def test_factor_gaps_overlaps_and_unknown_bases_fail_closed() -> None:
    """Even a day with no work needs a declared contribution factor schedule."""
    original = rule()
    first = original.alternatives[0]
    gap = first.model_copy(
        update={
            "factors": (factor("early", "0.1", START, START + timedelta(minutes=30)),),
        },
    )
    with pytest.raises(ValueError, match="factor coverage"):
        cost_contribution_activities(
            prices(),
            period(),
            original.model_copy(
                update={"alternatives": (gap, original.alternatives[1])},
            ),
            (),
        )
    with pytest.raises(ValueError, match="overlap"):
        ContributionAlternative.model_validate(
            first.model_copy(
                update={"factors": (factor("a", "0.1"), factor("b", "0.1"))},
            ).model_dump(),
        )


def test_unreviewed_hash_and_source_horizon_fail_closed() -> None:
    """Comparison and factor evidence must cover the whole declared period."""
    for bad in [
        rule().model_copy(update={"reviewed": False}),
        rule().model_copy(update={"source_sha256": "b" * 64}),
        rule().model_copy(update={"effective_to": date(2026, 1, 1)}),
    ]:
        with pytest.raises(ValueError, match=r"review|hash|period|dates"):
            cost_contribution_activities(prices(), period(), bad, (activity(),))
    original = rule()
    bad_factor = factor("bad", "0.1").model_copy(update={"source_sha256": "b" * 64})
    with pytest.raises(ValueError, match="hash"):
        cost_contribution_activities(
            prices(),
            period(),
            original.model_copy(
                update={
                    "alternatives": (
                        original.alternatives[0].model_copy(
                            update={"factors": (bad_factor,)},
                        ),
                        original.alternatives[1],
                    ),
                },
            ),
            (activity(),),
        )


def test_existing_contribution_is_not_added_twice() -> None:
    """A named output component already in the release cannot be charged again."""
    bad = rule().model_copy(update={"component": "salary"})
    with pytest.raises(ValueError, match=r"already|base"):
        cost_contribution_activities(prices(), period(), bad, (activity(),))


def test_independent_microsecond_factor_boundary_preserves_exact_quantities() -> None:
    """Factor boundaries split wage rows independently without Decimal drift."""
    boundary = START + timedelta(minutes=17, microseconds=1)
    original = rule()
    broad = original.alternatives[0].model_copy(
        update={
            "factors": (
                factor("early", "0.1", START, boundary),
                factor("late", "0.2", boundary, END),
            ),
        },
    )
    changed = original.model_copy(
        update={
            "alternatives": (broad, original.alternatives[1]),
        },
    )
    # Broad starts at 60 if .2 throughout, less .1 * 200 for 17min+1us.
    expected = Fraction(60) - Fraction(20) * Fraction(1020000001, 3600000000)
    with localcontext() as context:
        context.prec = 6
        result = cost_contribution_activities(
            prices(),
            period(),
            changed,
            (activity(),),
        )
    assert_that(result.contribution == expected)
    assert_that(result.exact_total == Fraction(300) + expected)
    assert_that(
        len([r for r in result.rows if r.alternative_id == "broad"]) == Fraction(3),
    )


def test_whole_period_source_horizon_is_required_even_without_earnings() -> None:
    """A source verified only through yesterday cannot authorize an empty period."""
    original = prices()
    registry = original.sources.model_copy(
        update={
            "records": (
                original.sources.records[0].model_copy(
                    update={
                        "effective_from": date(2025, 12, 31),
                        "verified_through": date(2026, 1, 1),
                    },
                ),
            ),
        },
    )
    with pytest.raises(ValueError, match="coverage"):
        cost_contribution_activities(
            original.model_copy(update={"sources": registry}),
            period(),
            rule(),
            (),
        )


def test_overlapping_and_duplicate_earnings_are_not_charged_twice() -> None:
    """Complete-history assertion does not bypass the base allocation checks."""
    for duplicate in (
        activity(),
        activity().model_copy(update={"activity_id": "other"}),
    ):
        with pytest.raises(ValueError, match=r"Duplicate|duplicate|overlap"):
            cost_contribution_activities(
                prices(),
                period(),
                rule(),
                (activity(), duplicate),
            )


def test_unsupported_caps_and_static_out_of_period_quantity_fail() -> None:
    """No silent cap omission, snapshot extrapolation or aggregate headcount."""
    with pytest.raises(ValueError, match="Unsupported"):
        cost_contribution_activities(
            prices(),
            period(),
            rule().model_copy(
                update={"required_capabilities": ("quarterly_cap",)},
            ),
            (),
        )
    for at, hours in ((END, "1"), (START, "2.0001")):
        with pytest.raises(ValueError, match="period"):
            cost_contribution_snapshot(
                prices(),
                period(),
                rule(),
                at,
                ResourceUse(resource_id="staff", hours=Decimal(hours)),
            )


def test_capped_earnings_use_prior_history_before_pricing() -> None:
    """A 2,500 remaining earnings base at 12 percent adds 300."""
    source = prices()
    source = source.model_copy(
        update={
            "rates": tuple(
                row.model_copy(update={"components": {"salary": Decimal(2500)}})
                for row in source.rates
            ),
        },
    )
    cap = ContributionCap(
        limit=Decimal(62500),
        prior_eligible_earnings=Decimal(60000),
        starts_at=datetime(2026, 1, 1, tzinfo=UTC),
        ends_at=datetime(2026, 4, 1, tzinfo=UTC),
        history_through=START,
        source_id="synthetic-award-1",
        source_sha256="a" * 64,
        citation="Synthetic cap evidence",
        reviewed=True,
    )
    alternative = ContributionAlternative(
        alternative_id="capped",
        bases=("salary",),
        factors=(factor("capped-rate", "0.12"),),
        cap=cap,
    )
    comparison = ContributionAlternative(
        alternative_id="comparison",
        bases=("salary",),
        factors=(factor("comparison-rate", "0.05"),),
    )
    capped_rule = rule().model_copy(update={"alternatives": (alternative, comparison)})
    dated = cost_contribution_activities(source, period(), capped_rule, (activity(),))
    snapshot = cost_contribution_snapshot(
        source,
        period(),
        capped_rule,
        START,
        ResourceUse(resource_id="staff", hours=Decimal(2)),
    )
    assert_that(dated.contribution == snapshot.contribution == Fraction(300))
    assert_that(
        [r.eligible_base_amount for r in dated.rows if r.alternative_id == "capped"]
        == [Fraction(2500), 0],
    )
    assert_that(
        [r.base_amount for r in dated.rows if r.alternative_id == "capped"]
        == [Fraction(2500), Fraction(2500)],
    )
    stale = cap.model_copy(update={"history_through": START - timedelta(hours=1)})
    invalid = capped_rule.model_copy(
        update={
            "alternatives": (alternative.model_copy(update={"cap": stale}), comparison),
        },
    )
    with pytest.raises(ValueError, match="history cutoff"):
        cost_contribution_activities(source, period(), invalid, (activity(),))

    changed = alternative.model_copy(
        update={
            "factors": (
                factor("early", "0.12", START, START + timedelta(hours=1)),
                factor("late", "0.18", START + timedelta(hours=1), END),
            ),
        },
    )
    changed_rule = capped_rule.model_copy(
        update={"alternatives": (changed, comparison)},
    )
    first = activity().model_copy(
        update={"activity_id": "first", "ends_at": START + timedelta(hours=1)},
    )
    second = activity().model_copy(
        update={"activity_id": "second", "starts_at": START + timedelta(hours=1)},
    )
    ordered = cost_contribution_activities(
        source,
        period(),
        changed_rule,
        (second, first),
    )
    assert_that(ordered.contribution == Fraction(300))


def test_planned_remittance_is_separate_from_earned_cost() -> None:
    """A later remittance remains an explicit timing assumption."""
    remittance = END + timedelta(days=14)
    dated = period().model_copy(update={"planned_remittance_at": remittance})
    result = cost_contribution_activities(prices(), dated, rule(), (activity(),))
    baseline = cost_contribution_activities(prices(), period(), rule(), (activity(),))
    assert_that(result.period.planned_remittance_at == remittance)
    assert_that(result.rows == baseline.rows)
    assert_that(result.exact_total == baseline.exact_total)
    resource = ResourceUse(resource_id="staff", hours=Decimal(2))
    snapshot = cost_contribution_snapshot(prices(), dated, rule(), START, resource)
    undated = cost_contribution_snapshot(prices(), period(), rule(), START, resource)
    assert_that(snapshot.period.planned_remittance_at == remittance)
    assert_that(snapshot.rows == undated.rows)
    assert_that(snapshot.exact_total == undated.exact_total)
    with pytest.raises(ValueError, match="remittance cannot precede"):
        cost_contribution_activities(
            prices(),
            dated.model_copy(update={"planned_remittance_at": START}),
            rule(),
            (activity(),),
        )


def test_paid_contribution_uses_posted_components_and_rejects_duplicates() -> None:
    """Price a payroll-only component using the reviewed posting basis."""
    original = rule()
    basis = original.alternatives[0].model_copy(update={"bases": ("vehicle",)})
    policy = original.model_copy(update={"alternatives": (basis,)})
    payment = ContributionPayment(
        payment_id="posting-1",
        resource_id="staff",
        allocation_id="worker",
        component="vehicle",
        paid_at=START,
        amount=Decimal(110),
        evidence="Synthetic posting receipt",
    )
    excluded = payment.model_copy(
        update={"payment_id": "posting-2", "component": "excluded"},
    )
    result = cost_contribution_payments(prices(), period(), policy, (excluded, payment))
    assert_that(result.contribution == Fraction(11))
    assert_that(tuple(row.payment for row in result.rows) == (payment,))
    with pytest.raises(ValueError, match="Duplicate contribution payment"):
        cost_contribution_payments(prices(), period(), policy, (payment, payment))
