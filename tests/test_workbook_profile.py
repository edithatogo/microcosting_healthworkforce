# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Candidate profile covers source cells without admitting conditions."""

from pathlib import Path

import pytest

from src.workbook_catalog import read_workbook_catalog
from src.workbook_profile import load_candidate_profile
from src.workbook_tables import extract_tables
from tests.checks import assert_that


def test_candidate_profile_reconciles_original_workbook() -> None:
    """Every populated cell is assigned, including unresolved sections."""
    catalog = read_workbook_catalog(Path("data/Labour Model - v3, 20240328.xlsx"))
    profile = load_candidate_profile()
    extraction = extract_tables(catalog, profile.table_definitions(catalog.sha256))
    expected_sections = 262
    expected_cells = 27929
    assert_that(len(extraction.tables) == expected_sections)
    assert_that(sum(len(table.cells) for table in extraction.tables) == expected_cells)
    assert_that(extraction.unassigned == ())
    assert_that(extraction.empty_sheets == ("Labour - BY (%)",))
    assert_that(
        any(
            table.definition.status == "physical_region_unresolved"
            for table in extraction.tables
        ),
    )
    for table in extraction.tables:
        for cell in table.cells:
            if cell.unit and isinstance(cell.source.value, str):
                assert_that(cell.source.excel_type == "f")


def test_candidate_profile_does_not_apply_to_other_source() -> None:
    """Coordinates from one historical workbook are never inferred for another."""
    with pytest.raises(ValueError, match="SHA-256"):
        load_candidate_profile().table_definitions("0" * 64)
