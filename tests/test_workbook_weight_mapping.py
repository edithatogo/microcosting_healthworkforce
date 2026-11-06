# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Check historical Medicare units, denominators and original cell lineage."""

from pathlib import Path

import pytest

from src.workbook_catalog import read_workbook_catalog
from src.workbook_profile import load_candidate_profile
from src.workbook_tables import extract_tables
from src.workbook_weight_mapping import weight_table_definitions
from tests.checks import assert_that


def test_weight_mapping_separates_count_types_and_formulas() -> None:
    """Cover every populated source cell without inferring workforce weights."""
    catalog = read_workbook_catalog(Path("data/Labour Model - v3, 20240328.xlsx"))
    result = extract_tables(catalog, weight_table_definitions(catalog.sha256))
    cells = {
        (table.definition.sheet, cell.coordinate): cell
        for table in result.tables
        for cell in table.cells
    }
    expected_cells = 263
    assert_that(len(cells) == expected_cells)
    assert_that(cells[("Medicare Enrolments", "B6")].unit == "cards")
    assert_that(cells[("Medicare Enrolments", "B19")].unit == "persons")
    assert_that(cells[("Medicare Enrolments", "B22")].unit == "persons/card")
    assert_that(
        cells[("Medicare Enrolments", "B30")].role == "historical_method_change",
    )
    assert_that(cells[("Weightings", "C10")].column_name == "five_state_denominator")
    assert_that(
        cells[("Weightings", "B10")].column_name == "australian_eligible_persons",
    )
    assert_that(cells[("Weightings", "H7")].role == "formula")
    assert_that(cells[("Weightings", "H2")].unit == "fraction")


def test_weight_mapping_rejects_other_workbook_versions() -> None:
    """Never silently apply reviewed coordinates to different workbook bytes."""
    with pytest.raises(ValueError, match="SHA-256"):
        weight_table_definitions("0" * 64)


def test_method_change_person_counts_have_consistent_archival_disposition() -> None:
    """The reviewed note identifies a historical signed count, never a weight."""
    catalog = read_workbook_catalog(Path("data/Labour Model - v3, 20240328.xlsx"))
    targeted = extract_tables(catalog, weight_table_definitions(catalog.sha256))
    profile = load_candidate_profile()
    complete = extract_tables(catalog, profile.table_definitions(catalog.sha256))
    for extraction in (targeted, complete):
        table = next(
            t
            for t in extraction.tables
            if t.definition.sheet == "Medicare Enrolments"
            and t.definition.area == "A29:B37"
        )
        assert_that(table.definition.status == "archived_candidate")
        cells = {c.coordinate: c for c in table.cells}
        assert_that(cells["B29"].unit is None)
        for row in range(30, 38):
            cell = cells[f"B{row}"]
            assert_that(cell.unit == "persons")
            assert_that(cell.column_name == "eligible_persons_method_change")
            assert_that(cell.role == "historical_method_change")
    note = next(
        c
        for sheet in catalog.sheets
        if sheet.name == "Medicare Enrolments"
        for c in sheet.cells
        if c.coordinate == "A28"
    )
    assert_that(isinstance(note.value, str))
    assert_that("September 2005" in str(note.value))
