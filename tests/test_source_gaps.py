# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Screening records must not treat keyword leads as applicable coverage."""

import pytest

from src.source_gaps import (
    CandidateSourceLink,
    DiscoveryLead,
    GapTarget,
    link_held_candidates,
    screen_gaps,
)
from src.source_registry import SourceRegistry
from tests.checks import assert_that
from tests.test_source_registry import source


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


def test_held_source_link_keeps_unassessed_status_and_existing_leads() -> None:
    """Holding a matching edition does not establish worker applicability."""
    target = GapTarget("QLD", "nursing", "public")
    lead = DiscoveryLead(
        "lead",
        "QLD",
        ("nursing",),
        "public",
        "lead",
        "https://example.org",
    )
    screened = screen_gaps((target,), (lead,))
    candidate = CandidateSourceLink(target, "synthetic-award-1", "candidate scope")
    result = link_held_candidates(
        screened,
        SourceRegistry(records=(source(),)),
        (candidate,),
    )
    assert_that(result[0].lead_ids == ("lead",))
    assert_that(result[0].status == "applicability_unassessed")
    assert_that(result[0].candidate_sources == (candidate,))
    assert_that(
        link_held_candidates(result, SourceRegistry(records=(source(),)), ()) == result,
    )


def test_source_links_reject_unknown_unheld_or_inconsistent_evidence() -> None:
    """No missing source, mismatched jurisdiction or duplicate is silently linked."""
    target = GapTarget("QLD", "nursing", "public")
    screened = screen_gaps((target,), ())
    held = SourceRegistry(records=(source(),))
    candidate = CandidateSourceLink(target, "synthetic-award-1", "candidate scope")
    with pytest.raises(ValueError, match="Duplicate"):
        link_held_candidates(screened, held, (candidate, candidate))
    invalid = (
        CandidateSourceLink(target, "missing", "scope"),
        CandidateSourceLink(target, "synthetic-award-1", " "),
        CandidateSourceLink(
            GapTarget("NSW", "nursing", "public"),
            "synthetic-award-1",
            "scope",
        ),
    )
    for item in invalid:
        with pytest.raises(ValueError, match="Candidate link"):
            link_held_candidates(screened, held, (item,))
    unheld = source(holding="referenced_only", sha256=None, applicability="unresolved")
    with pytest.raises(ValueError, match="held source"):
        link_held_candidates(screened, SourceRegistry(records=(unheld,)), (candidate,))
    other_jurisdiction = source(jurisdiction="NSW")
    with pytest.raises(ValueError, match="scope"):
        link_held_candidates(
            screened,
            SourceRegistry(records=(other_jurisdiction,)),
            (candidate,),
        )
