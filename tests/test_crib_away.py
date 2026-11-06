# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Require complete eligible crib evidence before pricing directed occasions."""

from datetime import date, datetime, timedelta
from decimal import Decimal, localcontext
from fractions import Fraction
from zoneinfo import ZoneInfo

import pytest

from src.crib_away import CribAwayRule, CribOccasion, CribShift, price_crib_away
from src.source_registry import SourceRegistry
from src.unit_quotes import UnitQuote, UnitQuoteRelease
from tests.checks import assert_that
from tests.test_source_registry import source

TWO_CRIBS = 2
OLDER_PRICE_YEAR = 2025


def rule(**changes: object) -> CribAwayRule:
    """Declare policy scope and context names without hard-coding an award."""
    values: dict[str, object] = {
        "rule_id": "synthetic-crib-policy",
        "one_crib_component": "single_context",
        "two_crib_component": "two_context",
        "unit": "directed_crib_occasion",
        "local_timezone": "Australia/Sydney",
        "interpretation_kind": "source_reviewed",
        "interpretation_basis": "Synthetic entitlement and occasion-date basis",
        "source_id": "synthetic-award-1",
        "source_sha256": "a" * 64,
        "citation": "Synthetic complete-slot policy",
        "reviewed": True,
        "effective_from": date(2026, 5, 15),
        "effective_to": date(2026, 11, 8),
        "as_known_on": date(2026, 11, 7),
        "jurisdiction": "QLD",
        "employer": "Synthetic employer",
        "classification": "Synthetic grade",
    }
    values.update(changes)
    return CribAwayRule.model_validate(values)


def release() -> UnitQuoteRelease:
    """Use independent synthetic prices; retain differences between alternatives."""
    quotes = tuple(
        UnitQuote(
            quote_id=f"{context}-{year}",
            component=context,
            unit="directed_crib_occasion",
            amount=Decimal(amount),
            starts_on=date(2026, 5, 15)
            if year == OLDER_PRICE_YEAR
            else date(2026, 7, 10),
            ends_on=date(2026, 7, 10)
            if year == OLDER_PRICE_YEAR
            else date(2026, 11, 8),
            known_from=date(2026, 1, 1),
            source_id="synthetic-award-1",
            source_sha256="a" * 64,
            citation="Synthetic each-occasion price",
            status="accepted",
        )
        for context, old, new in [
            ("single_context", "10.01", "11.01"),
            ("two_context", "5.01", "5.51"),
        ]
        for year, amount in [(2025, old), (2026, new)]
    )
    return UnitQuoteRelease(
        release_id="synthetic-crib-prices",
        currency="AUD",
        as_known_on=date(2026, 11, 7),
        jurisdiction="QLD",
        employer="Synthetic employer",
        classification="Synthetic grade",
        sources=SourceRegistry(records=(source(),)),
        quotes=quotes,
    )


def shift(**changes: object) -> CribShift:
    """Supply upstream eligible entitlement, not a guessed elapsed-hour rule."""
    values: dict[str, object] = {
        "shift_id": "shift-1",
        "resource_id": "opaque-resource",
        "starts_at": datetime(2026, 7, 10, 7, tzinfo=ZoneInfo("Australia/Sydney")),
        "ends_at": datetime(2026, 7, 10, 19, tzinfo=ZoneInfo("Australia/Sydney")),
        "entitled_cribs": 2,
        "eligibility_verified": True,
        "eligibility_basis": "Synthetic covered appointment",
        "entitlement_verified": True,
        "entitlement_basis": "Synthetic qualified roster and allowed break schedule",
        "history_complete": True,
        "input_kind": "analyst_assumption",
        "evidence_id": "synthetic-shift",
        "evidence_sha256": "b" * 64,
        "known_on": date(2026, 11, 7),
    }
    values.update(changes)
    return CribShift.model_validate(values)


def occasions() -> tuple[CribOccasion, ...]:
    """Supply each entitled slot, with direction explicitly true or false."""
    return tuple(
        CribOccasion(
            break_id=f"break-{slot}",
            shift_id="shift-1",
            slot=slot,
            occasion_at=datetime(
                2026,
                7,
                10,
                hour,
                tzinfo=ZoneInfo("Australia/Sydney"),
            ),
            directed_away=True,
            quote_id="two_context-2026",
            input_kind="analyst_assumption",
            evidence_id=f"synthetic-break-{slot}",
            evidence_sha256="c" * 64,
            known_on=date(2026, 11, 7),
            basis="Synthetic directed-away occasion, not payroll evidence",
        )
        for slot, hour in [(1, 12), (2, 16)]
    )


def test_one_and_two_contexts_preserve_each_occasion_and_cent_difference() -> None:
    """Two-crib price is each, not one bundled payment for both breaks."""
    two = price_crib_away(rule(), release(), shift(), occasions())
    one_break = occasions()[0].model_copy(update={"quote_id": "single_context-2026"})
    one = price_crib_away(
        rule(),
        release(),
        shift(entitled_cribs=1, ends_at=shift().ends_at - timedelta(hours=2)),
        (one_break,),
    )
    assert_that(two.pricing.total == Fraction(551, 50))
    assert_that(one.pricing.total == Fraction(1101, 100))
    assert_that(two.pricing.total - one.pricing.total == Fraction(1, 100))
    assert_that(two.directed_away_count == len(two.pricing.rows) == TWO_CRIBS)
    assert_that(all(r.quantity.quantity == 1 for r in two.pricing.rows))
    assert_that(two.mode == "scenario")


def test_known_non_away_slots_are_retained_without_creating_paid_units() -> None:
    """False direction is a known zero; it is not missing history."""
    first, second = occasions()
    second = second.model_copy(update={"directed_away": False, "quote_id": None})
    one = price_crib_away(rule(), release(), shift(), (first, second))
    assert_that(one.pricing.total == Fraction(551, 100))
    assert_that(one.directed_away_count == 1 and len(one.occasions) == TWO_CRIBS)
    first = first.model_copy(update={"directed_away": False, "quote_id": None})
    zero = price_crib_away(rule(), release(), shift(), (first, second))
    assert_that(zero.pricing.total == 0 and zero.pricing.rows == ())
    assert_that(len(zero.occasions) == TWO_CRIBS)


def test_dated_overnight_prices_and_json_roundtrip_remain_exact() -> None:
    """Explicit local occasion dates can straddle a supplied rate boundary."""
    zone = ZoneInfo("Australia/Sydney")
    case = shift(
        starts_at=datetime(2026, 7, 9, 18, tzinfo=zone),
        ends_at=datetime(2026, 7, 10, 6, tzinfo=zone),
    )
    first, second = occasions()
    first = first.model_copy(
        update={
            "occasion_at": datetime(2026, 7, 9, 23, tzinfo=zone),
            "quote_id": "two_context-2025",
        },
    )
    second = second.model_copy(
        update={"occasion_at": datetime(2026, 7, 10, 3, tzinfo=zone)},
    )
    rows = tuple(
        CribOccasion.model_validate_json(x.model_dump_json()) for x in [first, second]
    )
    with localcontext() as context:
        context.prec = 3
        result = price_crib_away(
            rule(),
            release(),
            CribShift.model_validate_json(case.model_dump_json()),
            rows,
        )
    assert_that(result.pricing.total == Fraction(263, 25))
    assert_that(
        [r.quantity.valued_on for r in result.pricing.rows]
        == [date(2026, 7, 9), date(2026, 7, 10)],
    )
    assert_that(result.occasions == rows)


def test_input_order_is_rebuilt_from_slot_order() -> None:
    """A caller's list order cannot change the chronological slot ledger."""
    result = price_crib_away(rule(), release(), shift(), tuple(reversed(occasions())))
    assert_that([o.slot for o in result.occasions] == [1, 2])


@pytest.mark.parametrize(
    "rows",
    [
        (),
        occasions()[:1],
        (*occasions(), occasions()[0]),
        (occasions()[0], occasions()[1].model_copy(update={"slot": 1})),
        (occasions()[0], occasions()[1].model_copy(update={"break_id": "break-1"})),
    ],
)
def test_incomplete_or_duplicate_history_is_rejected(
    rows: tuple[CribOccasion, ...],
) -> None:
    """Every entitled slot is required once, even when it is not directed away."""
    with pytest.raises(ValueError, match="distinct record"):
        price_crib_away(rule(), release(), shift(), rows)


@pytest.mark.parametrize(
    "change",
    [
        {"shift_id": "other"},
        {"occasion_at": shift().ends_at},
        {"occasion_at": shift().starts_at - timedelta(microseconds=1)},
        {"occasion_at": occasions()[0].occasion_at},
        {"occasion_at": occasions()[0].occasion_at - timedelta(minutes=1)},
        {"quote_id": "single_context-2026"},
        {"quote_id": "missing"},
        {"quote_id": "two_context-2025"},
        {"known_on": date(2026, 11, 8)},
        {"directed_away": None},
        {"slot": Decimal("1.5")},
        {"slot": True},
    ],
)
def test_forged_or_invalid_occasion_is_revalidated(change: dict[str, object]) -> None:
    """model_copy cannot bypass direction, cardinality, time, source or price checks."""
    rows = (occasions()[0], occasions()[1].model_copy(update=change))
    with pytest.raises(ValueError, match=r"belong|match|outside|knowledge|validation"):
        price_crib_away(rule(), release(), shift(), rows)


@pytest.mark.parametrize(
    "change",
    [
        {"eligibility_verified": False},
        {"entitlement_verified": False},
        {"history_complete": False},
        {"entitled_cribs": 3},
        {"entitled_cribs": True},
        {"known_on": date(2026, 11, 8)},
        {"ends_at": shift().starts_at},
    ],
)
def test_case_qualification_cannot_be_replaced_with_zero(
    change: dict[str, object],
) -> None:
    """Invalid case facts fail before monetary arithmetic."""
    with pytest.raises(ValueError, match=r"positive|verified|validation|knowledge"):
        price_crib_away(
            rule(),
            release(),
            shift().model_copy(update=change),
            occasions(),
        )


@pytest.mark.parametrize(
    "change",
    [
        {"reviewed": False},
        {"one_crib_component": "two_context"},
        {"source_sha256": "b" * 64},
        {"source_id": "missing"},
        {"effective_from": date(2026, 7, 11)},
        {"effective_to": date(2026, 7, 10)},
        {"employer": "Other"},
        {"classification": "Other"},
        {"as_known_on": date(2026, 11, 6)},
        {"unit": "hour"},
    ],
)
def test_policy_scope_and_alternative_prices_are_checked(
    change: dict[str, object],
) -> None:
    """A source citation alone cannot bypass dates, knowledge, scope or units."""
    with pytest.raises(
        ValueError,
        match=r"reviewed|hash|coverage|cover|matching|match",
    ):
        price_crib_away(
            rule().model_copy(update=change),
            release(),
            shift(),
            occasions(),
        )


def test_policy_source_must_be_known_and_present_in_release() -> None:
    """The legal-policy source is checked independently from price selection."""
    rates = release().model_copy(
        update={
            "sources": SourceRegistry(
                records=(
                    source(retrieved_at=datetime(2026, 11, 8, tzinfo=ZoneInfo("UTC"))),
                ),
            ),
        },
    )
    with pytest.raises(ValueError, match="knowledge"):
        price_crib_away(rule(), rates, shift(), occasions())


def test_observed_case_labels_require_completed_known_evidence() -> None:
    """Reviewed inputs retain their labels but cannot describe future observations."""
    case = shift(input_kind="observed_case_evidence")
    rows = tuple(
        o.model_copy(update={"input_kind": "observed_case_evidence"})
        for o in occasions()
    )
    result = price_crib_away(rule(), release(), case, rows)
    assert_that(result.mode == "reviewed_case_inputs")
    assert_that(
        all(r.quantity.quantity_kind == "observed_use" for r in result.pricing.rows),
    )
    with pytest.raises(ValueError, match="precede"):
        price_crib_away(
            rule(),
            release(),
            case.model_copy(update={"known_on": date(2026, 7, 9)}),
            rows,
        )
    bad = (rows[0].model_copy(update={"known_on": date(2026, 7, 9)}), rows[1])
    with pytest.raises(ValueError, match="precede"):
        price_crib_away(rule(), release(), case, bad)
    assumed = price_crib_away(
        rule(interpretation_kind="analyst_assumption"),
        release(),
        case,
        rows,
    )
    assert_that(assumed.mode == "scenario")


def test_naive_occasion_and_partial_policy_shift_fail() -> None:
    """Reject naive times and incomplete whole-shift policy coverage."""
    first, second = occasions()
    naive = first.model_copy(
        update={"occasion_at": first.occasion_at.replace(tzinfo=None)},
    )
    with pytest.raises(ValueError, match="timezone aware"):
        price_crib_away(rule(), release(), shift(), (naive, second))
    zone = ZoneInfo("Australia/Sydney")
    case = shift(
        starts_at=datetime(2026, 5, 14, 23, tzinfo=zone),
        ends_at=datetime(2026, 5, 15, 11, tzinfo=zone),
    )
    with pytest.raises(ValueError, match="cover"):
        price_crib_away(rule(), release(), case, (first, second))


def test_source_policy_is_required_independently_of_the_monetary_source() -> None:
    """A valid price source cannot substitute for missing/unknown policy evidence."""
    monetary = release()
    policy_source = source(
        source_id="separate-policy",
        sha256="d" * 64,
        retrieved_at=datetime(2026, 11, 8, tzinfo=ZoneInfo("UTC")),
    )
    rates = monetary.model_copy(
        update={"sources": SourceRegistry(records=(source(), policy_source))},
    )
    policy = rule(source_id="separate-policy", source_sha256="d" * 64)
    with pytest.raises(ValueError, match="policy source exceeds"):
        price_crib_away(policy, rates, shift(), occasions())
    with pytest.raises(ValueError, match="source coverage"):
        price_crib_away(policy, monetary, shift(), occasions())


def test_roster_entitlement_is_not_inferred_from_dst_elapsed_hours() -> None:
    """An explicit reviewed roster measure may differ from UTC elapsed hours."""
    zone = ZoneInfo("Australia/Sydney")
    case = shift(
        starts_at=datetime(2026, 10, 3, 20, tzinfo=zone),
        ends_at=datetime(2026, 10, 4, 8, tzinfo=zone),
        entitlement_basis="Synthetic 12-hour roster entitlement across DST",
    )
    first, second = occasions()
    rows = (
        first.model_copy(update={"occasion_at": datetime(2026, 10, 4, tzinfo=zone)}),
        second.model_copy(
            update={"occasion_at": datetime(2026, 10, 4, 5, tzinfo=zone)},
        ),
    )
    result = price_crib_away(rule(), release(), case, rows)
    assert_that(case.ends_at - case.starts_at == timedelta(hours=11))
    assert_that(result.directed_away_count == TWO_CRIBS)
    assert_that(result.pricing.total == Fraction(551, 50))


def test_injected_fractional_quantity_cannot_replace_one_occasion_unit() -> None:
    """The API constructs paid units; an extra fractional quantity field is invalid."""
    first, second = occasions()
    first = first.model_copy(update={"quantity": Decimal("1.5")})
    with pytest.raises(ValueError, match="Extra inputs"):
        price_crib_away(rule(), release(), shift(), (first, second))
