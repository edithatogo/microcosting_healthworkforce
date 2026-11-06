# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Exercise the reviewed legacy worksheet mapping against original cells."""

from pathlib import Path

import pytest

from src.workbook_catalog import read_workbook_catalog
from src.workbook_component_mapping import component_table_definitions
from src.workbook_tables import extract_tables
from tests.checks import assert_that


def test_component_mapping_preserves_numeric_and_display_distinction() -> None:
    """Separate historical amounts and shares from formatted aggregate text."""
    path = Path("data/Labour Model - v3, 20240328.xlsx")
    catalog = read_workbook_catalog(path)
    result = extract_tables(catalog, component_table_definitions(catalog.sha256))
    cells = {cell.coordinate: cell for table in result.tables for cell in table.cells}
    expected_populated_cells = 870
    assert_that(len(cells) == expected_populated_cells)
    assert_that(cells["C3"].unit == "AUD/year")
    assert_that(cells["C35"].unit == "fraction")
    assert_that(cells["C28"].role == "display_text")
    assert_that(cells["C60"].role == "display_text")
    assert_that(cells["C28"].unit is None)
    assert_that(cells["C2"].role is None)
    assert_that(cells["I3"].column_name == "professional_development")


def test_component_mapping_rejects_unreviewed_workbook() -> None:
    """Do not apply a reviewed coordinate mapping to different bytes."""
    with pytest.raises(ValueError, match="SHA-256"):
        component_table_definitions("0" * 64)
