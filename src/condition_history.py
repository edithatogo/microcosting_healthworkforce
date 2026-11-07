# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Explicit knowledge-dated selection of immutable condition release editions."""

import json
from hashlib import sha256
from typing import Self
lazy from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.conditions import ConditionRelease


class ReleaseEdition(BaseModel):
    """A released snapshot and the date it became available to the modeller."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    release: ConditionRelease
    known_from: date
    supersedes: str | None = None


class ReleasePin(BaseModel):
    """Exact replay identity and knowledge cutoff for a selected release."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    release_id: str = Field(min_length=1)
    release_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    knowledge_date: date


def release_sha256(release: ConditionRelease) -> str:
    """Hash complete canonical release content, including condition source scope."""
    release = ConditionRelease.model_validate(release.model_dump())
    legacy = release.as_known_at is None and all(
        item.retrospective is None for item in release.conditions
    )
    payload = release.model_dump(mode="json")
    if legacy:
        payload.pop("as_known_at")
    for item in payload["conditions"]:
        if item["workbook_origin"] is None:
            item.pop("workbook_origin")
        if legacy:
            item.pop("retrospective")
        if not any(condition.included_components for condition in release.conditions):
            item.pop("included_components")
    for source in payload["sources"]["records"]:
        if source["published_on"] is None:
            source.pop("published_on")
    encoded = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


class ConditionHistory(BaseModel):
    """A linear, scoped history; no unreviewed source is made applicable."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    editions: tuple[ReleaseEdition, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_lineage(self) -> Self:
        """Reject ambiguous chronology, changing scope and reused identities."""
        identities: set[str] = set()
        first = self.editions[0].release
        scope = (
            first.jurisdiction,
            first.employer,
            first.classification,
            first.method_id,
        )
        previous: ReleaseEdition | None = None
        for item in self.editions:
            release = item.release
            if (
                release.as_known_at is not None
                and item.known_from < release.as_known_at
            ):
                msg = "Release edition cannot predate its knowledge date"
                raise ValueError(msg)
            if release.release_id in identities:
                msg = "Release identities must be unique"
                raise ValueError(msg)
            identities.add(release.release_id)
            if (
                release.jurisdiction,
                release.employer,
                release.classification,
                release.method_id,
            ) != scope:
                msg = "Release history requires one scope and method"
                raise ValueError(msg)
            if previous is None:
                if item.supersedes is not None:
                    msg = "First release cannot supersede an absent edition"
                    raise ValueError(msg)
            elif (
                item.supersedes != previous.release.release_id
                or item.known_from <= previous.known_from
            ):
                msg = "Release editions require a linear, increasing knowledge history"
                raise ValueError(msg)
            previous = item
        return self

    def select(self, knowledge_date: date) -> tuple[ConditionRelease, ReleasePin]:
        """Choose the latest edition explicitly known on the supplied date."""
        history = ConditionHistory.model_validate(self.model_dump())
        eligible = [
            item for item in history.editions if item.known_from <= knowledge_date
        ]
        if not eligible:
            msg = "No release known at the requested knowledge date"
            raise ValueError(msg)
        release = eligible[-1].release
        return release, ReleasePin(
            release_id=release.release_id,
            release_sha256=release_sha256(release),
            knowledge_date=knowledge_date,
        )

    def replay(self, pin: ReleasePin) -> ConditionRelease:
        """Recover an explicitly pinned edition only if its bytes still match."""
        history = ConditionHistory.model_validate(self.model_dump())
        pin = ReleasePin.model_validate(pin.model_dump())
        edition = next(
            (
                item
                for item in history.editions
                if item.release.release_id == pin.release_id
            ),
            None,
        )
        if edition is None or edition.known_from > pin.knowledge_date:
            msg = "Pinned release was not known at the requested knowledge date"
            raise ValueError(msg)
        if release_sha256(edition.release) != pin.release_sha256:
            msg = "Pinned release content hash mismatch"
            raise ValueError(msg)
        return edition.release
