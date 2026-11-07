# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Retention boundaries must use complete history and actual receipt evidence."""

from datetime import date
from decimal import Decimal
from fractions import Fraction

import pytest

from src.retention import (
    PharmacyRetentionProration,
    PharmacyServicePortion,
    RetentionAssessment,
    RetentionAuthority,
    RetentionEvidence,
    RetentionHistorySegment,
    assess_pharmacy_retention,
    assess_retention,
    assess_retention_history,
    assess_sourced_retention,
    assessment_from_history,
    prorate_pharmacy_retention,
)
from tests.checks import assert_that
from tests.test_crib_away import release
lazy from src.unit_quotes import UnitQuoteRelease


def request(**changes: object) -> RetentionAssessment:
    """Provide explicit synthetic, fully qualified anniversary facts."""
    values: dict[str, object] = {
        "assessment_id": "synthetic-anniversary",
        "resource_id": "hypothetical-worker",
        "assessment_on": date(2026, 2, 6),
        "history_starts_on": date(2025, 2, 6),
        "history_ends_on": date(2026, 2, 6),
        "history_complete": True,
        "continuous_service_confirmed": True,
        "eligible_location_confirmed": True,
        "employment_eligible_confirmed": True,
        "annual_amount": Decimal(2000),
        "snapshot_fte": Fraction(1, 2),
        "unpaid_leave_weeks": Fraction(0),
        "competing_receipt": "not_received",
        "input_kind": "analyst_assumption",
        "basis": "Synthetic history, snapshot FTE and receipt facts only",
    }
    values.update(changes)
    return RetentionAssessment.model_validate(values)


def test_qualified_half_time_receives_half_annual_amount() -> None:
    """Snapshot FTE scales the qualified allowance once, not twice."""
    result = assess_retention(request())
    assert_that(result.amount == Fraction(1000))
    assert_that(result.scenario)


@pytest.mark.parametrize(
    ("weeks", "expected"),
    [(Fraction(3999, 1000), Fraction(1000)), (Fraction(4), Fraction(0))],
)
def test_four_week_unpaid_leave_boundary_is_discontinuous(
    weeks: Fraction,
    expected: Fraction,
) -> None:
    """Four weeks disqualifies rather than merely reducing a service fraction."""
    result = assess_retention(request(unpaid_leave_weeks=weeks))
    assert_that(result.amount == expected)


def test_actual_receipt_excludes_but_unknown_receipt_does_not_mean_no() -> None:
    """Unknown evidence must fail instead of creating a payable entitlement."""
    result = assess_retention(request(competing_receipt="received"))
    assert_that(result.amount == 0)
    with pytest.raises(ValueError, match="receipt"):
        assess_retention(request(competing_receipt="unknown"))


def test_incomplete_history_cannot_be_priced() -> None:
    """An absent service period is not assumed to be a complete eligible year."""
    with pytest.raises(ValueError, match=r"complete|history"):
        assess_retention(request(history_complete=False))


def sourced_inputs() -> tuple[RetentionAuthority, UnitQuoteRelease, RetentionEvidence]:
    """Bind synthetic anniversary price to known source and complete evidence."""
    r = release()
    q = r.quotes[-1].model_copy(
        update={
            "quote_id": "retention",
            "component": "retention",
            "unit": "anniversary_payment",
            "amount": Decimal(2000),
            "starts_on": date(2026, 2, 6),
        },
    )
    r = r.model_copy(update={"quotes": (q,)})
    authority = RetentionAuthority(
        rule_id="synthetic-clause53",
        source_id=q.source_id,
        source_sha256=q.source_sha256,
        citation="Synthetic anniversary policy",
        reviewed=True,
        effective_from=date(2026, 2, 6),
        effective_to=date(2026, 11, 8),
        jurisdiction=r.jurisdiction,
        employer=r.employer,
        classification=r.classification,
        quote_id=q.quote_id,
        interpretation_kind="analyst_assumption",
    )
    evidence = RetentionEvidence(
        evidence_id="synthetic-history",
        evidence_sha256="b" * 64,
        resource_id="hypothetical-worker",
        starts_on=date(2025, 2, 6),
        through_on=date(2026, 2, 6),
        known_on=date(2026, 11, 7),
        covered_facts=(
            "service",
            "location",
            "employment",
            "snapshot_fte",
            "unpaid_leave",
            "receipt",
        ),
        reviewed=True,
        input_kind="analyst_assumption",
        basis="Synthetic complete history and known nonreceipt",
    )
    return authority, r, evidence


def test_sourced_assessment_prices_exact_snapshot_once() -> None:
    """Qualified annual amount times snapshot FTE agrees with exact price ledger."""
    p, r, e = sourced_inputs()
    result, priced = assess_sourced_retention(p, r, request(), e)
    assert_that(result.amount == priced.total == Fraction(1000))
    assert_that(result.scenario)


@pytest.mark.parametrize(
    "change",
    [
        {"reviewed": False},
        {"source_sha256": "c" * 64},
        {"classification": "different"},
        {"effective_to": date(2026, 2, 6)},
    ],
)
def test_forged_authority_is_revalidated(change: dict[str, object]) -> None:
    """Frozen-model copies cannot bypass source, scope, review or dates."""
    p, r, e = sourced_inputs()
    with pytest.raises(ValueError, match="authority"):
        assess_sourced_retention(p.model_copy(update=change), r, request(), e)


@pytest.mark.parametrize(
    "change",
    [
        {"reviewed": False},
        {"resource_id": "other"},
        {"starts_on": date(2025, 2, 7)},
        {"through_on": date(2026, 2, 5)},
        {"known_on": date(2026, 11, 8)},
        {"covered_facts": ("service", "location")},
    ],
)
def test_incomplete_or_wrong_evidence_is_not_accepted(
    change: dict[str, object],
) -> None:
    """Coverage, resource and knowledge guards precede amount calculation."""
    p, r, e = sourced_inputs()
    with pytest.raises(ValueError, match="evidence"):
        assess_sourced_retention(p, r, request(), e.model_copy(update=change))


def test_sourced_known_receipt_retains_zero_price() -> None:
    """A qualified disqualification is an evidenced zero, not absent input."""
    p, r, e = sourced_inputs()
    result, priced = assess_sourced_retention(
        p,
        r,
        request(competing_receipt="received"),
        e,
    )
    assert_that(result.amount == priced.total == 0)
    assert_that("competing_receipt" in result.reasons)


def history_segment(**changes: object) -> RetentionHistorySegment:
    """Declare a complete hypothetical service year in explicit source units."""
    values: dict[str, object] = {
        "segment_id": "year",
        "evidence_id": "synthetic-year-evidence",
        "evidence_sha256": "b" * 64,
        "known_on": date(2026, 11, 7),
        "resource_id": "hypothetical-worker",
        "starts_on": date(2025, 2, 6),
        "ends_on": date(2026, 2, 6),
        "employed": True,
        "qualifying_location": True,
        "unpaid_leave_weeks": Fraction(0),
        "measurement_basis": "Hypothetical source-week measurement",
        "input_kind": "analyst_assumption",
    }
    values.update(changes)
    return RetentionHistorySegment.model_validate(values)


def test_history_aggregates_absence_across_segments_at_boundary() -> None:
    """Two separately recorded absences together reach the disqualifying boundary."""
    a = history_segment(ends_on=date(2025, 8, 6), unpaid_leave_weeks=Fraction(2))
    b = history_segment(
        segment_id="later",
        starts_on=date(2025, 8, 6),
        unpaid_leave_weeks=Fraction(2),
    )
    derived = assessment_from_history(request(), (b, a))
    assert_that(derived.unpaid_leave_weeks == Fraction(4))
    assert_that(assess_retention(derived).amount == 0)


@pytest.mark.parametrize("field", ["employed", "qualifying_location"])
def test_known_service_or_location_break_disqualifies(field: str) -> None:
    """A negative historical interval is retained rather than silently dropped."""
    derived = assessment_from_history(request(), (history_segment(**{field: False}),))
    assert_that(assess_retention(derived).amount == 0)


@pytest.mark.parametrize(
    "changes",
    [
        {"starts_on": date(2025, 2, 7)},
        {"ends_on": date(2026, 2, 5)},
        {"resource_id": "other"},
    ],
)
def test_missing_or_wrong_resource_history_fails(changes: dict[str, object]) -> None:
    """Missing intervals do not become zero absence or uninterrupted service."""
    with pytest.raises(ValueError, match="history"):
        assessment_from_history(request(), (history_segment(**changes),))


def test_dated_history_prices_and_retains_source_records() -> None:
    """History composition agrees with an independently qualified snapshot."""
    p, r, e = sourced_inputs()
    h = history_segment()
    result = assess_retention_history(p, r, request(), e, (h,))
    assert_that(result.prices.total == Fraction(1000))
    assert_that(result.history == (h,))
    assert_that(result.authority == p)
    assert_that(result.evidence == e)


@pytest.mark.parametrize(
    ("known", "kind"),
    [
        (date(2026, 11, 8), "analyst_assumption"),
        (date(2026, 2, 4), "observed_case_evidence"),
    ],
)
def test_history_evidence_dates_fail_closed(known: date, kind: str) -> None:
    """Future knowledge or an observation predating its interval is insufficient."""
    p, r, e = sourced_inputs()
    h = history_segment(known_on=known, input_kind=kind)
    with pytest.raises(ValueError, match="history evidence"):
        assess_retention_history(p, r, request(), e, (h,))


def pharmacy_request() -> PharmacyRetentionProration:
    """Reproduce the independent half-time, quarter-service 625 example."""
    return PharmacyRetentionProration(
        assessment_id="pharmacy-example",
        annual_amount=Decimal(5000),
        period_units=Fraction(100),
        unit="synthetic_service_units",
        portions=(
            PharmacyServicePortion(
                portion_id="worked",
                measured_units=Fraction(25),
                credit_fraction=Fraction(1),
                contracted_fte=Fraction(1, 2),
                category="service",
                basis="Synthetic credited service",
            ),
            PharmacyServicePortion(
                portion_id="outside",
                measured_units=Fraction(75),
                credit_fraction=Fraction(0),
                contracted_fte=Fraction(0),
                category="not_employed",
                basis="Synthetic nonemployment",
            ),
        ),
        allocation_method="credited_service_weighted_fte_v1",
        interpretation_kind="analyst_assumption",
        interpretation_basis="Synthetic denominator; policy allocation assumed",
        eligibility_confirmed=True,
        history_complete=True,
    )


def test_pharmacy_short_service_proration_is_not_general_disqualification() -> None:
    """A separately selected pharmacy method retains explicit short-service credit."""
    assert_that(prorate_pharmacy_retention(pharmacy_request()) == Fraction(625))


def test_pharmacy_rejects_forged_compensation_credit() -> None:
    """Compensation can continue market payments but never becomes retention service."""
    r = pharmacy_request()
    p = r.portions[0].model_copy(update={"category": "workers_compensation"})
    with pytest.raises(ValueError, match="zero credit"):
        prorate_pharmacy_retention(
            r.model_copy(update={"portions": (p, r.portions[1])}),
        )


def test_pharmacy_denominator_gap_is_not_zero_service() -> None:
    """Removing history fails rather than overstating or silently reducing payment."""
    r = pharmacy_request()
    with pytest.raises(ValueError, match="coverage"):
        prorate_pharmacy_retention(r.model_copy(update={"portions": r.portions[:1]}))


@pytest.mark.parametrize(
    "change",
    [
        {"amount": Decimal(3000)},
        {"unit": "hour"},
        {"starts_on": date(2026, 2, 7)},
    ],
)
def test_wrong_retention_quote_cannot_price_assessment(
    change: dict[str, object],
) -> None:
    """A scoped source alone cannot validate the wrong amount/unit/date quote."""
    p, r, e = sourced_inputs()
    r = r.model_copy(update={"quotes": (r.quotes[0].model_copy(update=change),)})
    with pytest.raises(ValueError, match="quote"):
        assess_sourced_retention(p, r, request(), e)


def test_history_overlap_and_duplicate_identity_fail() -> None:
    """Overlapping records cannot double-count service or absence."""
    h = history_segment()
    with pytest.raises(ValueError, match="unique"):
        assessment_from_history(request(), (h, h))
    other = h.model_copy(update={"segment_id": "other"})
    with pytest.raises(ValueError, match="overlaps"):
        assessment_from_history(request(), (h, other))


def test_history_empty_and_forged_interval_fail() -> None:
    """Neither absent evidence nor an invalid nested interval is accepted."""
    with pytest.raises(ValueError, match="nonempty"):
        assessment_from_history(request(), ())
    h = history_segment().model_copy(update={"ends_on": date(2025, 2, 6)})
    with pytest.raises(ValueError, match="positive"):
        assessment_from_history(request(), (h,))


@pytest.mark.parametrize(
    "change",
    [
        {"credit_fraction": Fraction(-1)},
        {"credit_fraction": Fraction(2)},
        {"contracted_fte": Fraction(2)},
        {"measured_units": Fraction(0)},
    ],
)
def test_forged_pharmacy_portion_bounds_fail(change: dict[str, object]) -> None:
    """Unvalidated copies cannot introduce negative or excessive service credit."""
    r = pharmacy_request()
    p = r.portions[0].model_copy(update=change)
    with pytest.raises(ValueError, match=r"greater|less"):
        prorate_pharmacy_retention(
            r.model_copy(update={"portions": (p, r.portions[1])}),
        )


def test_pharmacy_fraction_survives_json_roundtrip() -> None:
    """Exact service and FTE fractions do not become binary approximations."""
    r = PharmacyRetentionProration.model_validate_json(
        pharmacy_request().model_dump_json(),
    )
    assert_that(prorate_pharmacy_retention(r) == Fraction(625))


def test_pharmacy_bound_path_does_not_import_general_absence_threshold() -> None:
    """Four measured weeks do not override an independently reviewed credit factor."""
    p, r, e = sourced_inputs()
    p = p.model_copy(update={"method": "pharmacy_retention"})
    proration = pharmacy_request().model_copy(
        update={
            "assessment_id": "synthetic-anniversary",
            "annual_amount": Decimal(2000),
        },
    )
    result = assess_pharmacy_retention(
        p,
        r,
        request(unpaid_leave_weeks=Fraction(4)),
        e,
        proration,
    )
    assert_that(result.amount == result.prices.total == Fraction(250))
    assert_that(result.scenario)


def test_pharmacy_cannot_use_general_method() -> None:
    """Method selection is an explicit reviewed decision, not inferred from a price."""
    p, r, e = sourced_inputs()
    with pytest.raises(ValueError, match="pharmacy method"):
        assess_pharmacy_retention(p, r, request(), e, pharmacy_request())


def test_competing_receipt_does_not_reverse_pharmacy_priority() -> None:
    """Existing general payment needs settlement, not inverse exclusion."""
    p, r, e = sourced_inputs()
    p = p.model_copy(update={"method": "pharmacy_retention"})
    proration = pharmacy_request().model_copy(
        update={
            "assessment_id": "synthetic-anniversary",
            "annual_amount": Decimal(2000),
        },
    )
    with pytest.raises(ValueError, match="settlement"):
        assess_pharmacy_retention(
            p, r, request(competing_receipt="received"), e, proration,
        )
