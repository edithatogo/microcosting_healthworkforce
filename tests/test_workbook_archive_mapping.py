# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Qualify units, identity and source lineage for legacy sensitivity archives."""

from pathlib import Path

import pytest

from src.workbook_archive_mapping import archive_table_definitions
from src.workbook_catalog import read_workbook_catalog
from src.workbook_tables import extract_tables
from tests.checks import assert_that


def test_archived_long_tables_preserve_units_and_complete_cells() -> None:
    """Keep annual and hourly bounds distinct without treating them as draws."""
    catalog = read_workbook_catalog(Path("data/Labour Model - v3, 20240328.xlsx"))
    extraction = extract_tables(catalog, archive_table_definitions(catalog.sha256))
    cells = {
        (t.definition.table_id, c.coordinate): c
        for t in extraction.tables
        for c in t.cells
    }
    expected_cells = 7139
    assert_that(len(cells) == expected_cells)
    assert_that(cells[("dsa_annual_hourly_long", "D3")].unit == "AUD/year")
    assert_that(cells[("dsa_annual_hourly_long", "G3")].unit == "AUD/hour")
    assert_that(cells[("psa_labelled_annual_long", "D2")].role == "archived_bound")
    assert_that(cells[("psa_labelled_hourly_baseline", "D2")].unit == "AUD/hour")
    assert_that(cells[("dsa_annual_hourly_long", "D2")].role is None)
    for row in range(2, 332):
        for original_col, copy_col in zip("ABCGHI", "ABCDEF", strict=True):
            original = cells[("dsa_annual_hourly_long", f"{original_col}{row + 1}")]
            copy = cells[("dsa_hourly_long", f"{copy_col}{row}")]
            assert_that(original.source.value == copy.source.value)


def test_archived_mapping_rejects_another_source_version() -> None:
    """Coordinates are applicable only to the reviewed workbook hash."""
    with pytest.raises(ValueError, match="SHA-256"):
        archive_table_definitions("0" * 64)
