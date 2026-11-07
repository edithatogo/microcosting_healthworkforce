# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Preserve every worksheet and raw cell without inventing cached values."""

import hashlib
from datetime import time
lazy from pathlib import Path

import openpyxl
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.formula import ArrayFormula

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


def test_intake_preserves_array_formula_range_and_time(tmp_path: Path) -> None:
    """Keep the anchor formula, its output range and an independent time cell."""
    path = tmp_path / "array.xlsx"
    book = openpyxl.Workbook()
    sheet = book.create_sheet("Array")
    sheet["A1"] = ArrayFormula("A1:A2", "=ROW(A1:A2)")
    sheet["B1"] = time(8, 30)
    validation = DataValidation(type="whole", formula1="1", sqref="C1")
    sheet.add_data_validation(validation)
    book.save(path)
    book.close()

    catalog = read_workbook_catalog(path, sheet_names=("Array",))
    (rule,) = catalog.validations
    assert_that(rule.sheet == "Array" and "C1" in rule.rule_xml)
    assert_that(read_workbook_catalog(path, sheet_names=("Sheet",)).validations == ())
    (selected,) = catalog.sheets
    formula, clock = selected.cells
    assert_that(formula.value == "=ROW(A1:A2)" and formula.cached is None)
    assert_that(formula.array_formula_range == "A1:A2")
    assert_that(clock.value == clock.cached == time(8, 30))
    ranges = catalog.cells_frame()["array_formula_range"]
    assert_that(ranges.to_list() == ["A1:A2", None])
