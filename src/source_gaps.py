# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Keep occupation/sector gap targets separate from source discovery leads."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GapTarget:
    """A screening denominator, not a complete employer or occupation census."""

    jurisdiction: str
    profession_family: str
    sector: str


@dataclass(frozen=True)
class DiscoveryLead:
    """A potentially relevant item; inclusion does not prove applicability."""

    lead_id: str
    jurisdiction: str
    profession_families: tuple[str, ...]
    sector: str
    title: str
    uri: str


@dataclass(frozen=True)
class ScreenedGap:
    """Link matching leads while preserving unassessed scope and status."""

    target: GapTarget
    lead_ids: tuple[str, ...]
    status: str = "applicability_unassessed"


def screen_gaps(
    targets: tuple[GapTarget, ...],
    leads: tuple[DiscoveryLead, ...],
) -> tuple[ScreenedGap, ...]:
    """Associate only explicitly scoped leads without asserting coverage."""
    if len(set(targets)) != len(targets):
        msg = "Duplicate gap target"
        raise ValueError(msg)
    if len({lead.lead_id for lead in leads}) != len(leads):
        msg = "Duplicate discovery lead identity"
        raise ValueError(msg)
    if any(not all((lead.lead_id, lead.title, lead.uri)) for lead in leads):
        msg = "Discovery leads require identity, title and URI"
        raise ValueError(msg)
    return tuple(
        ScreenedGap(
            target,
            tuple(
                lead.lead_id
                for lead in leads
                if lead.jurisdiction == target.jurisdiction
                and target.profession_family in lead.profession_families
                and lead.sector == target.sector
            ),
        )
        for target in targets
    )
