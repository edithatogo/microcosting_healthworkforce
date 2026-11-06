# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Require evidence before source references become accepted cost inputs."""

from datetime import UTC, date, datetime
from hashlib import sha256
lazy from pathlib import Path

import pytest
from pydantic import ValidationError

from src.source_registry import SourceRecord, SourceRegistry
from tests.checks import assert_that


def source(**changes: object) -> SourceRecord:
    """Build a synthetic reference with explicit verification and scope."""
    values: dict[str, object] = {
        "source_id": "synthetic-award-1",
        "title": "Synthetic test instrument",
        "uri": "https://example.org/instrument",
        "edition": "test-1",
        "jurisdiction": "QLD",
        "kind": "agreement",
        "holding": "held",
        "authority": "primary",
        "applicability": "verified",
        "sha256": "a" * 64,
        "retrieved_at": datetime(2026, 1, 1, tzinfo=UTC),
        "effective_from": date(2026, 1, 1),
        "verified_through": date(2027, 1, 1),
        "employers": ("Synthetic employer",),
        "classifications": ("Synthetic grade",),
    }
    values.update(changes)
    return SourceRecord.model_validate(values)


def test_reference_is_not_applicable_evidence() -> None:
    """A URL without verified bytes and scope cannot qualify an entitlement."""
    with pytest.raises(ValidationError):
        source(holding="referenced_only", sha256=None)
    with pytest.raises(ValidationError):
        source(employers=())
    with pytest.raises(ValidationError):
        source(retrieved_at=datetime(2026, 1, 1, tzinfo=UTC).replace(tzinfo=None))


def test_registry_rejects_duplicate_identity_and_unknown_supersession() -> None:
    """Release lineage cannot ambiguously select a source."""
    with pytest.raises(ValidationError):
        SourceRegistry(records=(source(), source()))
    with pytest.raises(ValidationError):
        SourceRegistry(records=(source(supersedes=("missing",)),))


def test_nominal_expiry_does_not_end_applicability() -> None:
    """Only an explicit operative end stops selection, not nominal expiry."""
    registry = SourceRegistry(records=(source(nominal_expiry=date(2026, 1, 2)),))
    selected = registry.require_applicable(
        "synthetic-award-1",
        date(2026, 2, 1),
        "QLD",
        "Synthetic employer",
        "Synthetic grade",
    )
    assert_that(selected.source_id == "synthetic-award-1")
    with pytest.raises(ValueError, match="scope"):
        registry.require_applicable(
            selected.source_id,
            date(2026, 2, 1),
            "QLD",
            "Other",
            "Synthetic grade",
        )


def test_byte_verification_and_exclusive_evidence_horizon(tmp_path: Path) -> None:
    """A reviewed record still needs matching bytes and a bounded evidence date."""
    artifact = tmp_path / "instrument.txt"
    artifact.write_bytes(b"synthetic instrument")
    digest = sha256(artifact.read_bytes()).hexdigest()
    record = source(sha256=digest)
    record.verify_bytes(artifact)
    artifact.write_bytes(b"changed")
    with pytest.raises(ValueError, match="bytes"):
        record.verify_bytes(artifact)
    with pytest.raises(ValueError, match="scope"):
        SourceRegistry(records=(record,)).require_applicable(
            record.source_id,
            date(2027, 1, 1),
            "QLD",
            "Synthetic employer",
            "Synthetic grade",
        )
