# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Separate source holdings, authority and applicability for dated costing."""

from hashlib import sha256
from typing import Literal, Self
from urllib.parse import urlsplit
lazy from datetime import date, datetime
lazy from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SourceRecord(BaseModel):
    """Retain a source edition without inferring eligibility from its title."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    source_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    uri: str
    edition: str = Field(min_length=1)
    jurisdiction: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    holding: Literal["referenced_only", "held", "unavailable", "restricted"]
    authority: Literal["unverified", "primary", "secondary"] = "unverified"
    applicability: Literal[
        "unresolved",
        "verified",
        "conflicting",
        "not_applicable",
    ] = "unresolved"
    sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    retrieved_at: datetime | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    verified_through: date | None = None
    nominal_expiry: date | None = None
    employers: tuple[str, ...] = ()
    classifications: tuple[str, ...] = ()
    supersedes: tuple[str, ...] = ()
    reason: str = ""

    @field_validator("uri")
    @classmethod
    def public_uri(cls, value: str) -> str:
        """Retain source URLs without embedded credentials or unsupported schemes."""
        parsed = urlsplit(value)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
        ):
            message = "Source URI must be an HTTP(S) URL without credentials"
            raise ValueError(message)
        return value

    @model_validator(mode="after")
    def consistent_evidence(self) -> Self:
        """Require bytes and scoped verification before admitting applicability."""
        if self.retrieved_at is not None and self.retrieved_at.utcoffset() is None:
            message = "Source retrieval time must include a timezone"
            raise ValueError(message)
        if (self.holding == "held") != (self.sha256 is not None):
            message = "Only held sources have a required byte hash"
            raise ValueError(message)
        if self.holding == "held" and self.retrieved_at is None:
            message = "Held source requires retrieval time"
            raise ValueError(message)
        if self.effective_to is not None and (
            self.effective_from is None or self.effective_to <= self.effective_from
        ):
            message = "Source operative interval must be nonempty"
            raise ValueError(message)
        if self.applicability == "verified" and (
            self.holding != "held"
            or self.authority != "primary"
            or self.effective_from is None
            or self.verified_through is None
            or self.verified_through <= self.effective_from
            or not self.employers
            or not self.classifications
        ):
            message = "Verified applicability requires held primary bytes and scope"
            raise ValueError(message)
        if self.applicability == "not_applicable" and not self.reason.strip():
            message = "Not-applicable sources require a reason"
            raise ValueError(message)
        return self

    def verify_bytes(self, path: Path) -> None:
        """Verify an explicitly selected local artifact without changing its status."""
        if (
            self.holding != "held"
            or sha256(path.read_bytes()).hexdigest() != self.sha256
        ):
            message = "Source bytes do not match the held edition"
            raise ValueError(message)


class SourceRegistry(BaseModel):
    """Freeze a set of unique source editions and their supersession lineage."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    schema_version: Literal[1] = 1
    records: tuple[SourceRecord, ...]

    @model_validator(mode="after")
    def unique_lineage(self) -> Self:
        """Reject duplicate IDs, missing lineage targets and cycles."""
        by_id = {r.source_id: r for r in self.records}
        if len(by_id) != len(self.records):
            message = "Duplicate source identity"
            raise ValueError(message)
        visited: set[str] = set()
        active: set[str] = set()

        def visit(identity: str) -> None:
            if identity in active or identity not in by_id:
                message = "Cyclic or unknown source supersession"
                raise ValueError(message)
            if identity in visited:
                return
            active.add(identity)
            for parent in by_id[identity].supersedes:
                visit(parent)
            active.remove(identity)
            visited.add(identity)

        for identity in by_id:
            visit(identity)
        return self

    def require_applicable(
        self,
        source_id: str,
        when: date,
        jurisdiction: str,
        employer: str,
        classification: str,
    ) -> SourceRecord:
        """Resolve exact verified scope; nominal expiry does not end operation."""
        record = next((r for r in self.records if r.source_id == source_id), None)
        if (
            record is None
            or record.applicability != "verified"
            or record.jurisdiction != jurisdiction
            or employer not in record.employers
            or classification not in record.classifications
            or record.effective_from is None
            or when < record.effective_from
            or (record.effective_to is not None and when >= record.effective_to)
            or record.verified_through is None
            or when >= record.verified_through
        ):
            message = "No verified source coverage for the requested scope and date"
            raise ValueError(message)
        return record
