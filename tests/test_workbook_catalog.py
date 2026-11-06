# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Preserve every worksheet and raw cell without inventing cached values."""

import hashlib
lazy from pathlib import Path

import openpyxl
from openpyxl.workbook.defined_name import DefinedName

from src.workbook_catalog import read_workbook_catalog
from tests.checks import assert_that


def test_complete_intake_preserves_formula_names_and_empty_sheet(
    tmp_path: Path,
) -> None:
    """Raw formulas, merged headers, local names and empty tabs remain traceable."""
    path = tmp_path / "synthetic.xlsx"
    book = openpyxl.Workbook()
    sheet = book.active
    assert_that(sheet is not None)
    if sheet is None:
        raise AssertionError
    sheet.title = "Inputs"
    sheet.append(["Role", "Rate"])
    sheet.append(["Synthetic", 10])
    sheet["C2"] = "=B2*2"
    sheet["A4"] = "Notes"
    sheet["A4"].hyperlink = "https://example.org/source"
    sheet.merge_cells("A4:B4")
    sheet.defined_names.add(DefinedName("LocalTitle", attr_text="'Inputs'!$A$1"))
    book.create_sheet("Empty")
    book.save(path)
    book.close()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    catalog = read_workbook_catalog(path)
    assert_that(catalog.sha256 == digest)
    assert_that(hashlib.sha256(path.read_bytes()).hexdigest() == digest)
    assert_that([s.name for s in catalog.sheets] == ["Inputs", "Empty"])
    assert_that(catalog.sheets[1].cells == ())
    assert_that(catalog.sheets[0].regions == ("A1:C2", "A4:A4"))
    formula = next(c for c in catalog.sheets[0].cells if c.coordinate == "C2")
    assert_that(formula.value == "=B2*2" and formula.cached is None)
    assert_that(catalog.sheets[0].defined_names["LocalTitle"] == "'Inputs'!$A$1")
    expected_cells = 6
    assert_that(catalog.cells_frame().height == expected_cells)
    assert_that(catalog.sheets[0].merged_ranges == ("A4:B4",))
