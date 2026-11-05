# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Screening records must not treat keyword leads as applicable coverage."""

import pytest

from src.source_gaps import DiscoveryLead, GapTarget, screen_gaps
from tests.checks import assert_that


def test_leads_remain_unverified_and_are_scoped() -> None:
    """A potentially relevant document is neither a holding nor an entitlement."""
    target = GapTarget("NSW", "nursing", "public")
    other = GapTarget("QLD", "nursing", "public")
    lead = DiscoveryLead(
        "award-1",
        "NSW",
        ("nursing",),
        "public",
        "title",
        "https://example.org/a",
    )
    screened = screen_gaps((target, other), (lead,))
    assert_that(screened[0].lead_ids == ("award-1",))
    assert_that(screened[0].status == "applicability_unassessed")
    assert_that(screened[1].lead_ids == ())


def test_duplicate_target_and_lead_ids_are_rejected() -> None:
    """Denominator and identities remain stable under report generation."""
    target = GapTarget("NSW", "medical", "public")
    with pytest.raises(ValueError, match="Duplicate"):
        screen_gaps((target, target), ())
