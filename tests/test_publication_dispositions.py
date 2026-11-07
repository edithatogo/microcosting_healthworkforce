# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Keep publication displays, identity labels and unknown scalars distinct."""

from pathlib import Path

from src.workbook_catalog import read_workbook_catalog
from src.workbook_profile import load_candidate_profile
from src.workbook_tables import TableExtraction, extract_tables
from tests.checks import assert_that


def extracted() -> TableExtraction:
    """Read the pinned original using explicit candidate definitions."""
    catalog = read_workbook_catalog(Path("data/Labour Model - v3, 20240328.xlsx"))
    return extract_tables(
        catalog,
        load_candidate_profile().table_definitions(catalog.sha256),
    )


def test_publication_literals_are_display_text_and_labels() -> None:
    """Display strings never become accepted numeric intervals or pay rates."""
    table = next(
        t
        for t in extracted().tables
        if t.definition.table_id == "WS10-R01-display_other_below"
    )
    cells = {c.coordinate: c for c in table.cells}
    assert_that(table.definition.status == "archived_candidate")
    for row in range(35, 65):
        c = cells[f"AK{row}"]
        assert_that(c.role == "presentation" and c.unit is None)
        assert_that(c.column_name == "flattened_hourly_bounds_display")
        assert_that(isinstance(c.source.value, str) and c.source.excel_type != "f")
    for row in range(37, 42):
        assert_that(cells[f"AM{row}"].role == "identity")
        assert_that(cells[f"AM{row}"].column_name == "wide_display_personnel_type")
        assert_that(cells[f"AN{row}"].role == "identity")
        assert_that(
            cells[f"AN{row}"].column_name == "wide_display_sensitivity_variable",
        )
        assert_that(cells[f"AM{row}"].unit is None and cells[f"AN{row}"].unit is None)


def test_empty_declared_column_does_not_invent_a_missing_value() -> None:
    """The pinned empty column has a physical disposition, not guessed intent."""
    table = next(
        t
        for t in extracted().tables
        if t.definition.table_id == "WS10-R01-display_other_below"
    )
    meaning = next(c for c in table.definition.columns if c.column == "AL")
    assert_that(meaning.role == "unpopulated_layout")
    assert_that(meaning.unit is None)
    empty_column_index = 38
    assert_that(not any(c.source.column == empty_column_index for c in table.cells))


def test_psa_title_is_a_label_while_scalar_meaning_remains_unknown() -> None:
    """A scalar's title does not establish its unit, estimand or a PSA oracle."""
    table = next(t for t in extracted().tables if t.definition.table_id == "WS20-R01")
    cells = {c.coordinate: c for c in table.cells}
    assert_that(table.definition.header_rows == (1,))
    assert_that(cells["A1"].role is None and cells["A1"].unit is None)
    assert_that(cells["A2"].role == "unresolved_historical_value")
    assert_that(cells["A2"].unit is None)
    assert_that(table.definition.status == "archived_candidate")


def test_unresolved_historical_values_are_preserved_without_units() -> None:
    """Both unresolved numeric cells stay distinct from priced conditions."""
    unresolved = {
        (table.definition.sheet, cell.coordinate): (cell.unit, table.definition.status)
        for table in extracted().tables
        for cell in table.cells
        if cell.role == "unresolved_historical_value"
    }
    assert_that(
        unresolved
        == {
            ("Labour - Prices (DSA)", "AK39"): (None, "physical_region_unresolved"),
            ("PSA - Validation", "A2"): (None, "archived_candidate"),
        },
    )
