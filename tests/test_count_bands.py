# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Count bands require complete facts, source coverage and explicit quantities."""

from datetime import UTC, date, datetime
from decimal import Decimal, localcontext
from fractions import Fraction

import pytest

from src.count_bands import (
    CountBand,
    CountBandCase,
    CountBandFact,
    CountBandRule,
    price_count_bands,
)
from src.exclusive_quotes import QuoteExposureWindow
from src.source_registry import SourceRegistry
from src.unit_quotes import UnitQuote, UnitQuoteRelease
from tests.checks import assert_that
from tests.test_exclusive_quotes import allocation, rule
from tests.test_source_registry import source

OLDER_PRICE_YEAR = 2025

NAMES = ("small", "medium", "large", "largest")


def policy() -> CountBandRule:
    """Fictional count thresholds with explicit no-entitlement for zero/one."""
    bands = (CountBand(band_id="below-minimum", minimum=0, maximum=1, component=None),)
    bands += tuple(
        CountBand(band_id=name, minimum=lo, maximum=hi, component=name)
        for name, lo, hi in zip(NAMES, (2, 6, 11, 16), (5, 10, 15, 19), strict=True)
    )
    return CountBandRule(
        scope=rule(components=NAMES, unit="week"),
        bands=bands,
        required_facts=("qualifying_role", "required_duties", "selection_or_relief"),
    )


def release() -> UnitQuoteRelease:
    """Independent synthetic weekly prices; no real award data is published."""
    quotes = tuple(
        UnitQuote(
            quote_id=f"{name}-{year}",
            component=name,
            unit="week",
            amount=Decimal(str(amount)),
            starts_on=date(2026, 5, 15)
            if year == OLDER_PRICE_YEAR
            else date(2026, 7, 10),
            ends_on=date(2026, 7, 10)
            if year == OLDER_PRICE_YEAR
            else date(2026, 11, 8),
            known_from=date(2026, 1, 1),
            source_id="synthetic-award-1",
            source_sha256="a" * 64,
            citation="Synthetic band price",
            status="accepted",
        )
        for name, old, new in zip(
            NAMES,
            (10, 20, 30, 40),
            (11, 22, 33, 44),
            strict=True,
        )
        for year, amount in [(2025, old), (2026, new)]
    )
    return UnitQuoteRelease(
        release_id="synthetic-bands",
        currency="AUD",
        as_known_on=date(2026, 11, 7),
        jurisdiction="QLD",
        employer="Synthetic employer",
        classification="Synthetic grade",
        sources=SourceRegistry(records=(source(),)),
        quotes=quotes,
    )


def case(count: int = 2, **changes: object) -> CountBandCase:
    """Declare constant count/facts and reviewed units for one allocation."""
    a = allocation()
    exposure = QuoteExposureWindow.model_validate(
        {k: v for k, v in dict(a).items() if k != "quote_id"},
    )
    values: dict[str, object] = {
        "exposure": exposure,
        "staff_count": count,
        "count_and_facts_constant": True,
        "facts": tuple(
            CountBandFact(
                fact_id=name,
                satisfied=True,
                effective_from=date(2026, 5, 15),
                effective_to=date(2026, 11, 8),
                basis="Synthetic reviewed fact",
                input_kind="observed_case_evidence",
                known_on=date(2026, 11, 7),
                evidence_id=name + "-evidence",
                evidence_sha256="b" * 64,
            )
            for name in policy().required_facts
        ),
    }
    values.update(changes)
    return CountBandCase.model_validate(values)


@pytest.mark.parametrize(
    ("count", "amount"),
    [
        (0, 0),
        (1, 0),
        (2, 11),
        (5, 11),
        (6, 22),
        (10, 22),
        (11, 33),
        (15, 33),
        (16, 44),
        (19, 44),
    ],
)
def test_band_boundaries_select_one_price_without_maximizing(
    count: int,
    amount: int,
) -> None:
    """Both ends are inclusive; higher-priced other bands are not alternatives."""
    result = price_count_bands(policy(), release(), (case(count),))
    selected = result.selections[0]
    assert_that(result.prices.total == Fraction(amount))
    assert_that(selected.amount == result.prices.total)
    assert_that(selected.case.staff_count == count)
    assert_that(selected.band.minimum <= count <= selected.band.maximum)
    assert_that(not result.scenario)
    assert_that(result.release == release())


def test_unknown_count_above_published_band_fails_even_if_zero_or_ineligible() -> None:
    """Unknown bands cannot become zero or reuse the last published price."""
    c = case(20)
    for x in [
        c,
        c.model_copy(
            update={"exposure": c.exposure.model_copy(update={"quantity": Decimal(0)})},
        ),
        c.model_copy(
            update={
                "facts": tuple(
                    f.model_copy(update={"satisfied": False}) for f in c.facts
                ),
            },
        ),
    ]:
        with pytest.raises(ValueError, match="count band"):
            price_count_bands(policy(), release(), (x,))


def test_known_negative_fact_retains_suppressed_price_and_original_quantity() -> None:
    """Known false differs from missing or unknown, while preserving the price."""
    c = case(6)
    c = c.model_copy(
        update={
            "facts": (c.facts[0].model_copy(update={"satisfied": False}), *c.facts[1:]),
        },
    )
    result = price_count_bands(policy(), release(), (c,))
    row = result.selections[0]
    assert_that(result.prices.total == 0)
    assert_that(row.quote is not None and row.quote.amount == Decimal(22))
    assert_that(row.case.exposure.quantity == Decimal(1))
    assert_that(row.disqualifying_facts == ("qualifying_role",))
    assert_that(result.prices.rows[0].quantity.quantity == Decimal(0))


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "duplicate",
        "extra",
        "unknown",
        "future",
        "uncovered-window",
        "not-constant",
    ],
)
def test_incomplete_or_invalid_fact_evidence_fails(change: str) -> None:
    """Every required predicate is known and temporally qualified, even at zero."""
    c = case(0)
    facts = c.facts
    if change == "missing":
        facts = facts[:-1]
    elif change == "duplicate":
        facts = (facts[0], facts[0], facts[2])
    elif change == "extra":
        facts += (facts[0].model_copy(update={"fact_id": "extra"}),)
    elif change == "unknown":
        facts = (facts[0].model_copy(update={"satisfied": None}), *facts[1:])
    elif change == "future":
        facts = (
            facts[0].model_copy(update={"known_on": date(2026, 11, 8)}),
            *facts[1:],
        )
    elif change == "uncovered-window":
        facts = (
            facts[0].model_copy(update={"effective_to": date(2026, 7, 10)}),
            *facts[1:],
        )
    c = c.model_copy(
        update={"facts": facts, "count_and_facts_constant": change != "not-constant"},
    )
    with pytest.raises(ValueError, match=r"fact|constant|boolean"):
        price_count_bands(policy(), release(), (c,))


def test_dynamic_count_and_price_changes_equal_explicit_snapshot_sum() -> None:
    """One old small week10 plus one new medium week22 equals32."""
    a = case(2)
    b = case(6)
    a = a.model_copy(
        update={
            "exposure": a.exposure.model_copy(
                update={
                    "starts_at": datetime(2026, 7, 9, tzinfo=UTC),
                    "ends_at": datetime(2026, 7, 9, 1, tzinfo=UTC),
                    "valued_on": date(2026, 7, 9),
                },
            ),
        },
    )
    b = b.model_copy(
        update={"exposure": b.exposure.model_copy(update={"allocation_id": "second"})},
    )
    dynamic = price_count_bands(policy(), release(), (b, a))
    assert_that(dynamic.prices.total == Fraction(32))
    assert_that(
        dynamic.prices.total
        == sum(
            (price_count_bands(policy(), release(), (c,)).prices.total for c in (a, b)),
            Fraction(0),
        ),
    )
    assert_that(tuple(s.case.staff_count for s in dynamic.selections) == (2, 6))


def test_fractional_quantities_aggregate_exactly_in_low_decimal_precision() -> None:
    """Three independently allocated thirds of a weekly price11 equal11."""
    base = case()
    cases = tuple(
        base.model_copy(
            update={
                "exposure": base.exposure.model_copy(
                    update={
                        "allocation_id": str(i),
                        "resource_id": str(i),
                        "quantity": Fraction(1, 3),
                    },
                ),
            },
        )
        for i in range(3)
    )
    with localcontext() as context:
        context.prec = 3
        result = price_count_bands(policy(), release(), cases)
    assert_that(result.prices.total == Fraction(11))
    assert_that(all(s.amount == Fraction(11, 3) for s in result.selections))


@pytest.mark.parametrize(
    "change",
    ["overlap", "duplicate-band", "unknown-component", "duplicate-fact", "blank-fact"],
)
def test_invalid_rule_copies_are_revalidated(change: str) -> None:
    """Band and predicate identities cannot be forged after construction."""
    p = policy()
    bands = p.bands
    facts = p.required_facts
    if change == "overlap":
        bands = (bands[0].model_copy(update={"maximum": 2}), *bands[1:])
    elif change == "duplicate-band":
        bands = (bands[0], bands[0], *bands[2:])
    elif change == "unknown-component":
        bands = (
            bands[0],
            bands[1].model_copy(update={"component": "unknown"}),
            *bands[2:],
        )
    elif change == "duplicate-fact":
        facts = ("same", "same")
    elif change == "blank-fact":
        facts = (" ",)
    with pytest.raises(ValueError, match=r"band|fact|component"):
        price_count_bands(
            p.model_copy(update={"bands": bands, "required_facts": facts}),
            release(),
            (case(),),
        )


def test_price_change_inside_window_requires_explicit_split_even_when_ineligible() -> (
    None
):
    """Neither a false fact nor zero quantity can hide incomplete price coverage."""
    c = case()
    c = c.model_copy(
        update={
            "exposure": c.exposure.model_copy(
                update={
                    "starts_at": datetime(2026, 7, 9, tzinfo=UTC),
                    "quantity": Decimal(0),
                },
            ),
            "facts": tuple(f.model_copy(update={"satisfied": False}) for f in c.facts),
        },
    )
    with pytest.raises(ValueError, match="whole window"):
        price_count_bands(policy(), release(), (c,))


def test_duplicate_and_overlapping_allocations_rejected() -> None:
    """Count selection retains shared nonduplication and complete-history guards."""
    c = case()
    for cases in [
        (c, c),
        (
            c,
            c.model_copy(
                update={
                    "exposure": c.exposure.model_copy(
                        update={"allocation_id": "other"},
                    ),
                },
            ),
        ),
    ]:
        with pytest.raises(ValueError, match=r"unique|overlap"):
            price_count_bands(policy(), release(), cases)


def test_scenario_fact_propagates_even_when_it_suppresses_payment() -> None:
    """A scenario label survives a negative upstream predicate and zero result."""
    c = case()
    c = c.model_copy(
        update={
            "facts": (
                c.facts[0].model_copy(
                    update={"satisfied": False, "input_kind": "analyst_assumption"},
                ),
                *c.facts[1:],
            ),
        },
    )
    assert_that(price_count_bands(policy(), release(), (c,)).scenario)


@pytest.mark.parametrize("change", ["source", "hash", "knowledge", "unit", "history"])
def test_zero_count_does_not_bypass_source_or_exposure_guards(change: str) -> None:
    """Even an explicit no-entitlement band needs fully qualified inputs."""
    p = policy()
    r = release()
    c = case(0)
    if change == "source":
        r = r.model_copy(
            update={
                "sources": SourceRegistry(
                    records=(source(applicability="unresolved"),),
                ),
            },
        )
    elif change == "hash":
        p = p.model_copy(
            update={"scope": p.scope.model_copy(update={"source_sha256": "c" * 64})},
        )
    elif change == "knowledge":
        p = p.model_copy(
            update={
                "scope": p.scope.model_copy(update={"as_known_on": date(2026, 11, 6)}),
            },
        )
    elif change == "unit":
        c = case(2)
        p = p.model_copy(update={"scope": p.scope.model_copy(update={"unit": "hour"})})
    else:
        c = c.model_copy(
            update={
                "exposure": c.exposure.model_copy(update={"history_complete": False}),
            },
        )
    with pytest.raises(
        ValueError,
        match=r"applicability|source|hash|knowledge|window|history",
    ):
        price_count_bands(p, r, (c,))


def test_dst_duration_does_not_become_a_weekly_quantity() -> None:
    """One explicit week stays one week across a one-hour spring clock change."""
    c = case()
    c = c.model_copy(
        update={
            "exposure": c.exposure.model_copy(
                update={
                    "starts_at": datetime(2026, 10, 3, 15, tzinfo=UTC),
                    "ends_at": datetime(2026, 10, 3, 16, tzinfo=UTC),
                    "valued_on": date(2026, 10, 4),
                    "input_kind": "analyst_assumption",
                    "selection_basis": (
                        "One explicitly allocated week; no elapsed-hour proration"
                    ),
                },
            ),
        },
    )
    result = price_count_bands(policy(), release(), (c,))
    assert_that(result.prices.total == Fraction(11))
    assert_that(result.prices.rows[0].quantity.quantity == Decimal(1))
    assert_that(result.scenario)


@pytest.mark.parametrize("count", [-1, True, Decimal(2)])
def test_count_copies_cannot_bypass_strict_integer_validation(count: object) -> None:
    """Negative, boolean and decimal counts are not qualified integer evidence."""
    with pytest.raises(ValueError, match=r"greater than|integer"):
        price_count_bands(
            policy(),
            release(),
            (case().model_copy(update={"staff_count": count}),),
        )


def test_earlier_known_fact_uses_explicit_effective_coverage_without_redating() -> None:
    """A qualification learned earlier can cover a later fully evidenced window."""
    c = case()
    facts = tuple(f.model_copy(update={"known_on": date(2026, 1, 1)}) for f in c.facts)
    c = c.model_copy(update={"facts": facts})
    result = price_count_bands(policy(), release(), (c,))
    assert_that(result.prices.total == Fraction(11))
    assert_that(
        all(f.known_on == date(2026, 1, 1) for f in result.selections[0].case.facts),
    )


def test_invalid_fact_interval_is_revalidated() -> None:
    """Unchecked updates cannot forge an effective fact interval."""
    c = case()
    f = c.facts[0].model_copy(update={"effective_to": c.facts[0].effective_from})
    with pytest.raises(ValueError, match="effective coverage"):
        price_count_bands(
            policy(),
            release(),
            (c.model_copy(update={"facts": (f, *c.facts[1:])}),),
        )
