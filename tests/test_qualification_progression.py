# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Check qualification boundaries before pay-point selection."""

from datetime import date
from fractions import Fraction

import pytest

from src.qualification_progression import (
    ProgressionBarrier,
    ProgressionRequest,
    WeeklyQualificationAllowance,
    assess_progression,
    price_progression_week,
)
from src.source_registry import SourceRegistry
from tests.checks import assert_that
from tests.test_source_registry import source
from tests.test_unit_quotes import quote, release


@pytest.mark.parametrize("first_gated_year", [4, 5])
def test_progression_checks_the_proposed_year_and_reviewed_qualification(
    first_gated_year: int,
) -> None:
    """The boundary and exact alternatives are explicit inputs."""
    held = source()
    registry = SourceRegistry(records=(held,))
    day = date(2026, 6, 1)
    barrier = ProgressionBarrier(
        source_id=held.source_id,
        source_sha256="a" * 64,
        citation="Synthetic qualification rule",
        jurisdiction=held.jurisdiction,
        employer=held.employers[0],
        classification=held.classifications[0],
        as_known_on=day,
        reviewed=True,
        first_gated_year=first_gated_year,
        accepted_codes=frozenset({"degree", "membership"}),
    )
    request = ProgressionRequest(
        valued_on=day,
        proposed_year=first_gated_year,
        qualification_codes=frozenset({"allowance-only"}),
        known_on=day,
        evidence_id="synthetic-case",
        reviewed=True,
    )
    assert_that(not assess_progression(barrier, request, registry).permitted)
    below = request.model_copy(update={"proposed_year": first_gated_year - 1})
    assert_that(assess_progression(barrier, below, registry).permitted)
    qualified = request.model_copy(
        update={"qualification_codes": frozenset({"membership"})},
    )
    decision = assess_progression(barrier, qualified, registry)
    assert_that(decision.permitted and decision.source == held)
    later = qualified.model_copy(update={"known_on": date(2026, 6, 2)})
    with pytest.raises(ValueError, match="knowledge horizon"):
        assess_progression(barrier, later, registry)
    with pytest.raises(ValueError, match="held and known"):
        assess_progression(
            barrier.model_copy(update={"source_sha256": "b" * 64}),
            qualified,
            registry,
        )

    prices = release(quote(quote_id="wage", unit="week")).model_copy(
        update={"as_known_on": day},
    )
    mapping = {first_gated_year: "wage"}
    with pytest.raises(ValueError, match="qualifying credential"):
        price_progression_week(prices, barrier, request, mapping)
    with pytest.raises(ValueError, match="mapped weekly wage"):
        price_progression_week(prices, barrier, qualified, {})
    priced_decision, cost = price_progression_week(prices, barrier, qualified, mapping)
    assert_that(priced_decision == decision)
    assert_that(cost.total == Fraction("100.01"))

    allowance = WeeklyQualificationAllowance(
        quote_id="credential",
        accepted_codes=frozenset({"allowance-only"}),
        minimum_year_in_receipt=first_gated_year,
        year_in_receipt=first_gated_year - 1,
    )
    prices = release(
        quote(quote_id="wage", unit="week"),
        quote(quote_id="credential", component="allowance", unit="week"),
    ).model_copy(update={"as_known_on": day})
    both = qualified.model_copy(
        update={"qualification_codes": frozenset({"membership", "allowance-only"})},
    )
    _, below_allowance = price_progression_week(
        prices,
        barrier,
        both,
        mapping,
        allowance=allowance,
    )
    assert_that(below_allowance.total == Fraction("100.01"))
    eligible = allowance.model_copy(update={"year_in_receipt": first_gated_year})
    _, combined = price_progression_week(
        prices,
        barrier,
        both,
        mapping,
        allowance=eligible,
    )
    assert_that(combined.total == Fraction("200.02"))
    assert_that(
        tuple(row.quote.quote_id for row in combined.rows) == ("wage", "credential"),
    )
    _, progression_only = price_progression_week(
        prices,
        barrier,
        qualified,
        mapping,
        allowance=eligible,
    )
    assert_that(progression_only.total == Fraction("100.01"))
