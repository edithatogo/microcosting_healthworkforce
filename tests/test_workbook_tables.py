# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Test traceable table segmentation without inferring spreadsheet semantics."""

lazy from pathlib import Path

import openpyxl
import pytest

from src.workbook_catalog import read_workbook_catalog
from src.workbook_tables import ColumnMeaning, TableDefinition, extract_tables
from tests.checks import assert_that


def test_tables_preserve_cells_units_and_unknown_disposition(tmp_path: Path) -> None:
    """Split stacked tables while keeping original coordinates and explicit units."""
    path = tmp_path / "tables.xlsx"
    book = openpyxl.Workbook()
    sheet = book["Sheet"]
    sheet.title = "Components"
    sheet.append(["role", "percentage"])
    sheet.append(["nurse", 120])
    sheet.append(["role", "percentage"])
    sheet.append(["nurse", 0.2])
    book.create_sheet("Empty")
    book.save(path)
    book.close()
    catalog = read_workbook_catalog(path)
    definitions = (
        TableDefinition(
            "dollars",
            "Components",
            "A1:B2",
            "archive",
            "cost",
            (ColumnMeaning("B", "component", "AUD", "value"),),
        ),
        TableDefinition(
            "shares",
            "Components",
            "A3:B4",
            "archive",
            "share",
            (ColumnMeaning("B", "component", "fraction", "value"),),
        ),
    )
    result = extract_tables(catalog, definitions)
    assert_that(result.unassigned == ())
    assert_that(result.empty_sheets == ("Empty",))
    assert_that(result.tables[0].cells[1].unit == "AUD")
    assert_that(result.tables[1].cells[-1].unit == "fraction")
    assert_that(result.tables[1].cells[-1].coordinate == "B4")
    assert_that(result.tables[0].cells[0].unit is None)


def test_overlapping_or_unmatched_definitions_fail(tmp_path: Path) -> None:
    """A source cell cannot be silently assigned twice or to an unknown sheet."""
    path = tmp_path / "book.xlsx"
    book = openpyxl.Workbook()
    sheet = book["Sheet"]
    sheet["A1"] = "hello"
    book.save(path)
    book.close()
    catalog = read_workbook_catalog(path)
    first = TableDefinition("a", "Sheet", "A1:A1", "candidate", "unknown")
    second = TableDefinition("b", "Sheet", "A1:B2", "candidate", "unknown")
    with pytest.raises(ValueError, match="overlap"):
        extract_tables(catalog, (first, second))
    missing = TableDefinition("c", "missing", "A1:A1", "candidate", "unknown")
    with pytest.raises(ValueError, match="sheet"):
        extract_tables(catalog, (missing,))
