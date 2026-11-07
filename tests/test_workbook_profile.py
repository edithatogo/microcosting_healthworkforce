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
    expected_sections = 267
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


def test_all_component_formulas_expose_first_jurisdiction_salary_basis() -> None:
    """Preserve the historical aggregation without making it an accepted mean."""
    catalog = read_workbook_catalog(Path("data/Labour Model - v3, 20240328.xlsx"))
    profile = load_candidate_profile()
    extraction = extract_tables(catalog, profile.table_definitions(catalog.sha256))
    table = next(t for t in extraction.tables if t.definition.table_id == "WS01-R13")
    cells = {cell.coordinate: cell for cell in table.cells}
    for offset in range(5):
        rows = tuple(start + offset for start in (28, 22, 16, 10, 4))
        for column in "JMNOPQST":
            refs = ",".join(f"{column}{row}" for row in rows)
            weeks = "/52" if column == "S" else ""
            cell = cells[f"{column}{77 + offset}"]
            assert_that(cell.source.value == f"=AVERAGE({refs}){weeks}*$W{4 + offset}")
            assert_that(cell.role == "mean_input_first_jurisdiction_salary")
        for column in "RVWX":
            refs = ",".join(f"{column}{row}" for row in rows)
            cell = cells[f"{column}{77 + offset}"]
            assert_that(cell.source.value == f"=AVERAGE({refs})")
            assert_that(cell.unit == "AUD/year")


def test_primary_component_formulas_and_candidate_meanings() -> None:
    """Check every jurisdiction-role component against its actual formula basis."""
    catalog = read_workbook_catalog(Path("data/Labour Model - v3, 20240328.xlsx"))
    profile = load_candidate_profile()
    extraction = extract_tables(catalog, profile.table_definitions(catalog.sha256))
    tables = {table.definition.table_id: table for table in extraction.tables}
    columns = ("J", "M", "N", "O", "P", "Q", "R", "S", "T", "V", "W", "X")
    meanings = (
        "superannuation",
        "average_penalties",
        "public_holiday_penalty",
        "private_practice_loading",
        "attraction_retention_allowance",
        "sick_leave_proxy",
        "professional_development_allowance",
        "annual_leave_proxy",
        "annual_leave_loading_proxy",
        "salary_lower",
        "salary_midpoint",
        "salary_upper",
    )
    for block, (source, dollars, shares) in enumerate(
        zip(
            (4, 10, 16, 22, 28),
            (47, 53, 59, 65, 71),
            (90, 96, 102, 108, 114),
            strict=True,
        ),
    ):
        dollar_table = tables[f"WS01-R{8 + block:02}"]
        share_table = tables[f"WS01-R{15 + block:02}"]
        dollar_cells = {cell.coordinate: cell for cell in dollar_table.cells}
        share_cells = {cell.coordinate: cell for cell in share_table.cells}
        for offset in range(5):
            row = source + offset
            for column, meaning in zip(columns, meanings, strict=True):
                term = f"{column}{row}"
                if column in "JMNOPQT":
                    term += f"*$W{row}"
                elif column == "S":
                    term += f"/52*$W{row}"
                expected_dollar = f"=({term})" if column in "JMNOPQST" else f"={term}"
                amount = dollar_cells[f"{column}{dollars + offset}"]
                share = share_cells[f"{column}{shares + offset}"]
                assert_that(amount.source.value == expected_dollar)
                assert_that(share.source.value == f"=({term})/$Z{row}")
                assert_that(amount.unit == "AUD/year" and share.unit == "fraction")
                assert_that(amount.column_name == f"{meaning}_annual")
                assert_that(share.column_name == f"{meaning}_share_of_midpoint_cost")
                if column in ("V", "X"):
                    assert_that(amount.role == share.role == "alternative_salary_bound")


def test_publication_comparisons_preserve_formula_derived_roles() -> None:
    """All 120 ratios retain their actual numerator and denominator lineage."""
    catalog = read_workbook_catalog(Path("data/Labour Model - v3, 20240328.xlsx"))
    extraction = extract_tables(
        catalog,
        load_candidate_profile().table_definitions(catalog.sha256),
    )
    tables = {table.definition.table_id: table for table in extraction.tables}
    roles = (
        "administrative_staff",
        "bioinformatics_staff",
        "lab_technician",
        "medical_scientist",
        "pathologists",
    )
    for index, denominator in enumerate(roles):
        table = tables[f"WS10-R01-comparison-{index + 1}"]
        cells = {cell.coordinate: cell for cell in table.cells}
        numerator_indices = [i for i in range(5) if i != index]
        for offset in range(6):
            row = 2 + 7 * index + offset
            for column, numerator_index in zip(
                ("BD", "BE", "BF", "BG"),
                numerator_indices,
                strict=True,
            ):
                cell = cells[f"{column}{row}"]
                numerator_row = 2 + 7 * numerator_index + offset
                expected_formula = f"=BC{numerator_row}/BC{row}"
                assert_that(str(cell.source.value).replace("$", "") == expected_formula)
                assert_that(
                    cell.column_name == f"{roles[numerator_index]}_over_{denominator}",
                )
                assert_that(cell.unit == "ratio" and cell.role == "formula_ratio")
        for column in ("BD", "BE", "BF", "BG"):
            header = cells[f"{column}{1 + 7 * index}"]
            assert_that(header.unit is None and header.role is None)
    assert_that(tables["WS10-R01-comparison-1"].cells[0].source.value == "BI")
    third = {cell.coordinate: cell for cell in tables["WS10-R01-comparison-3"].cells}
    assert_that(third["BE15"].source.value == "BS")
    assert_that(third["BE16"].column_name == "bioinformatics_staff_over_lab_technician")
