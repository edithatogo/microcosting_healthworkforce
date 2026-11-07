# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Check later-of commencement and source admission."""

from datetime import date

import pytest

from src.advancement_effective import (
    AdvancementEvidence,
    AdvancementRule,
    resolve_advancement_commencement,
)
from src.source_registry import SourceRegistry
from tests.checks import assert_that
from tests.test_source_registry import source


@pytest.mark.parametrize(("received", "expected"), [(1, 3), (3, 3), (5, 5)])
def test_commencement_uses_later_date_and_preserves_evidence(
    received: int,
    expected: int,
) -> None:
    """Applications before, on or after the service boundary price from that date."""
    held = source()
    rule = AdvancementRule(
        source_id=held.source_id,
        source_sha256="a" * 64,
        citation="Synthetic progression clause",
        jurisdiction=held.jurisdiction,
        employer=held.employers[0],
        classification=held.classifications[0],
        as_known_on=date(2026, 6, 10),
        reviewed=True,
    )
    evidence = AdvancementEvidence(
        service_completed_on=date(2026, 6, 2),
        application_received_on=date(2026, 6, received),
        known_on=date(2026, 6, 6),
        evidence_id="synthetic-case",
        evidence_sha256="b" * 64,
        reviewed=True,
    )
    registry = SourceRegistry(records=(held,))
    result = resolve_advancement_commencement(rule, evidence, registry)
    assert_that(result.effective_from == date(2026, 6, expected))
    assert_that(result.day_after_service == date(2026, 6, 3))
    assert_that(result.evidence == evidence)
    assert_that(result.source == held)
    with pytest.raises(ValueError, match="knowledge horizon"):
        resolve_advancement_commencement(
            rule.model_copy(update={"as_known_on": date(2026, 6, 1)}),
            evidence,
            registry,
        )
    with pytest.raises(ValueError, match="held and known"):
        resolve_advancement_commencement(
            rule.model_copy(update={"source_sha256": "c" * 64}),
            evidence,
            registry,
        )
