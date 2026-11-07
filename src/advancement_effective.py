# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Resolve advancement after a reviewed service and application threshold."""

from dataclasses import dataclass
from datetime import date, timedelta

from pydantic import Field

from src.source_registry import SourceRecord, SourceRegistry
from src.unit_quotes import QuoteModel


class AdvancementEvidence(QuoteModel):
    """Reviewed dates and opaque evidence for a qualified application."""

    service_completed_on: date
    application_received_on: date
    known_on: date
    evidence_id: str
    evidence_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reviewed: bool


class AdvancementRule(QuoteModel):
    """Source and scope for the later-of commencement rule."""

    source_id: str
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    citation: str
    jurisdiction: str
    employer: str
    classification: str
    as_known_on: date
    reviewed: bool


@dataclass(frozen=True)
class AdvancementCommencement:
    """Retain the exact inputs and both candidate commencement dates."""

    rule: AdvancementRule
    evidence: AdvancementEvidence
    source: SourceRecord
    day_after_service: date
    effective_from: date


def resolve_advancement_commencement(
    rule: AdvancementRule,
    evidence: AdvancementEvidence,
    sources: SourceRegistry,
) -> AdvancementCommencement:
    """Use the later of application receipt and the day after service completion.

    The evidence supplies the reviewed service threshold date, including any
    continuity and calendar conventions. Qualification, appointment eligibility,
    payment processing and later progression remain separate decisions.
    """
    rule = AdvancementRule.model_validate(rule.model_dump())
    evidence = AdvancementEvidence.model_validate(evidence.model_dump())
    sources = SourceRegistry.model_validate(sources.model_dump())
    if not rule.reviewed or not evidence.reviewed:
        msg = "Advancement requires reviewed rule and eligibility evidence"
        raise ValueError(msg)
    if not (
        max(evidence.service_completed_on, evidence.application_received_on)
        <= evidence.known_on
        <= rule.as_known_on
    ):
        msg = "Advancement evidence dates exceed the knowledge horizon"
        raise ValueError(msg)
    if evidence.service_completed_on == date.max:
        msg = "Service completion must allow a following day"
        raise ValueError(msg)
    day_after_service = evidence.service_completed_on + timedelta(days=1)
    effective_from = max(day_after_service, evidence.application_received_on)
    source = sources.require_applicable(
        rule.source_id,
        effective_from,
        rule.jurisdiction,
        rule.employer,
        rule.classification,
    )
    if (
        source.sha256 != rule.source_sha256
        or source.retrieved_at is None
        or source.retrieved_at.date() > rule.as_known_on
    ):
        msg = "Advancement source must match the held and known edition"
        raise ValueError(msg)
    return AdvancementCommencement(
        rule,
        evidence,
        source,
        day_after_service,
        effective_from,
    )
