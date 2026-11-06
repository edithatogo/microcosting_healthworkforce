# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Keep occupation/sector gap targets separate from source discovery leads."""

from dataclasses import dataclass, replace

lazy from src.source_registry import SourceRegistry


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
    candidate_sources: tuple[CandidateSourceLink, ...] = ()


@dataclass(frozen=True)
class CandidateSourceLink:
    """A reasoned association with held bytes, not an applicability decision."""

    target: GapTarget
    source_id: str
    rationale: str


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


def link_held_candidates(
    screened: tuple[ScreenedGap, ...],
    sources: SourceRegistry,
    links: tuple[CandidateSourceLink, ...],
) -> tuple[ScreenedGap, ...]:
    """Attach explicit held-source candidates without asserting coverage.

    The source jurisdiction must match. Profession, employer, sector,
    effective dates and instrument precedence still require separate review.
    """
    sources = SourceRegistry.model_validate(sources.model_dump())
    targets = {item.target for item in screened}
    if len(targets) != len(screened):
        msg = "Duplicate screened gap target"
        raise ValueError(msg)
    if any(item.status != "applicability_unassessed" for item in screened):
        msg = "Candidate linking requires unassessed screening status"
        raise ValueError(msg)
    if any(
        link.target != item.target
        for item in screened
        for link in item.candidate_sources
    ):
        msg = "Existing candidate link does not match its screened target"
        raise ValueError(msg)
    all_links = (
        tuple(link for item in screened for link in item.candidate_sources) + links
    )
    by_source = {source.source_id: source for source in sources.records}
    seen: set[tuple[GapTarget, str]] = set()
    for link in all_links:
        key = (link.target, link.source_id)
        source = by_source.get(link.source_id)
        if key in seen:
            msg = "Duplicate candidate source link"
            raise ValueError(msg)
        seen.add(key)
        if (
            link.target not in targets
            or not link.rationale.strip()
            or source is None
            or source.holding != "held"
            or source.jurisdiction != link.target.jurisdiction
        ):
            msg = "Candidate link requires a held source, target, scope and rationale"
            raise ValueError(msg)
    return tuple(
        replace(
            item,
            candidate_sources=tuple(
                link for link in all_links if link.target == item.target
            ),
        )
        for item in screened
    )
