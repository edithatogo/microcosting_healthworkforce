# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Load a versioned candidate workbook profile without accepting its values."""

from importlib.resources import files

from pydantic import BaseModel, ConfigDict, Field

from src.workbook_tables import ColumnMeaning, TableDefinition


class CandidateColumn(BaseModel):
    """One provisional column meaning; absent units remain unresolved."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    column: str
    name: str
    unit: str | None
    role: str


class CandidateTable(BaseModel):
    """One explicitly scoped physical or candidate semantic section."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    table_id: str
    sheet: str
    area: str
    status: str
    purpose: str
    columns: list[CandidateColumn]
    header_rows: list[int]

    def definition(self) -> TableDefinition:
        """Convert metadata into the lossless table extraction contract."""
        return TableDefinition(
            self.table_id,
            self.sheet,
            self.area,
            self.status,
            self.purpose,
            tuple(ColumnMeaning(**column.model_dump()) for column in self.columns),
            tuple(self.header_rows),
        )


class CandidateProfile(BaseModel):
    """A candidate coordinate profile, distinct from an accepted release."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    workbook_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    definitions: list[CandidateTable]
    empty_sheets: list[str]
    unassigned: list[list[str]]
    limitations: str

    def table_definitions(self, workbook_sha256: str) -> tuple[TableDefinition, ...]:
        """Apply coordinates only to the exact source workbook."""
        if workbook_sha256 != self.workbook_sha256:
            msg = "Candidate profile requires the reviewed workbook SHA-256"
            raise ValueError(msg)
        return tuple(table.definition() for table in self.definitions)


def load_candidate_profile() -> CandidateProfile:
    """Read bundled metadata; raw workbook contents are not included."""
    content = (
        files("src")
        .joinpath("workbook_candidate_profile.json")
        .read_text(
            encoding="utf-8",
        )
    )
    return CandidateProfile.model_validate_json(content)
