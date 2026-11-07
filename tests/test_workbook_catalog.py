# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Preserve every worksheet and raw cell without inventing cached values."""

import hashlib
from datetime import time
from zipfile import ZipFile
lazy from pathlib import Path

import openpyxl
import pytest
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
    book.defined_names.add(DefinedName("LocalTitle", attr_text="Inputs!$B$1"))
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
    assert_that(catalog.defined_name_at("Inputs", "localtitle")[0] == "Inputs")
    assert_that(catalog.defined_name_at("Empty", "localtitle") == (None, "Inputs!$B$1"))
    with pytest.raises(KeyError, match="UnknownName"):
        catalog.defined_name_at("Inputs", "UnknownName")
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
    assert_that(rule.targets == ("C1",))
    assert_that(rule.formula1 == "1")
    assert_that(rule.formula2 is None)
    assert_that(read_workbook_catalog(path, sheet_names=("Sheet",)).validations == ())
    (selected,) = catalog.sheets
    formula, clock = selected.cells
    assert_that(formula.value == "=ROW(A1:A2)" and formula.cached is None)
    assert_that(formula.array_formula_range == "A1:A2")
    assert_that(clock.value == clock.cached == time(8, 30))
    ranges = catalog.cells_frame()["array_formula_range"]
    assert_that(ranges.to_list() == ["A1:A2", None])


def test_intake_retains_extended_validation(tmp_path: Path) -> None:
    """Read a validation extension that openpyxl omits from its model."""
    original = tmp_path / "original.xlsx"
    extended = tmp_path / "extended.xlsx"
    book = openpyxl.Workbook()
    book.save(original)
    book.close()
    extension = (
        b'<extLst><ext uri="{CCE6A557-97BC-4B89-ADB6-D9C93CAAB3DF}">'
        b'<x14:dataValidations xmlns:x14="http://schemas.microsoft.com/office/'
        b'spreadsheetml/2009/9/main" xmlns:xm="http://schemas.microsoft.com/'
        b'office/excel/2006/main" count="1">'
        b'<x14:dataValidation type="list"><x14:formula1><xm:f>INDIRECT($J6)</xm:f>'
        b"</x14:formula1><xm:sqref>K6:K55</xm:sqref></x14:dataValidation>"
        b"</x14:dataValidations></ext></extLst>"
    )
    with ZipFile(original) as source, ZipFile(extended, "w") as target:
        for name in source.namelist():
            data = source.read(name)
            if name == "xl/worksheets/sheet1.xml":
                data = data.replace(b"</worksheet>", extension + b"</worksheet>")
            target.writestr(name, data)

    with pytest.warns(UserWarning, match="Data Validation extension"):
        catalog = read_workbook_catalog(extended)
    (rule,) = catalog.validations
    assert_that(rule.sheet == "Sheet")
    assert_that(rule.targets == ("K6:K55",))
    assert_that(rule.validation_type == "list")
    assert_that(rule.operator == "between")
    assert_that(not rule.allow_blank)
    assert_that(rule.formula1 == "INDIRECT($J6)")
    assert_that(rule.formula2 is None)
    assert_that(rule.formulas_at("K55") == ("INDIRECT($J55)", None))
    assert_that(rule.formulas_at("$K$55") == ("INDIRECT($J55)", None))
    with pytest.raises(ValueError, match="one unqualified cell"):
        rule.formulas_at("K54:K55")
    with pytest.raises(ValueError, match="outside the validation range"):
        rule.formulas_at("K56")
    assert_that("INDIRECT($J6)" in rule.rule_xml and "K6:K55" in rule.rule_xml)


def test_intake_rejects_document_type_before_parsing(tmp_path: Path) -> None:
    """Reject declarations before either workbook reader parses the XML."""
    path = tmp_path / "doctype.xlsx"
    xml = "<!DOCTYPE workbook><workbook/>"
    with ZipFile(path, "w") as archive:
        archive.writestr("xl/workbook.xml", xml.encode("utf-16"))
    with pytest.raises(ValueError, match="document type declaration"):
        read_workbook_catalog(path)
