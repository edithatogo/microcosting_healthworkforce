# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Trace historical aggregate DSA columns without accepting their assumptions."""

import re
from pathlib import Path

from openpyxl.utils import column_index_from_string, get_column_letter

from src.workbook_catalog import read_workbook_catalog
from src.workbook_profile import load_candidate_profile
from src.workbook_tables import extract_tables
from tests.checks import assert_that


def test_aggregate_axes_preserve_original_formula_lineage() -> None:
    """The five ALL rows retain ten scenario axes and both output units."""
    catalog = read_workbook_catalog(Path("data/Labour Model - v3, 20240328.xlsx"))
    extraction = extract_tables(
        catalog,
        load_candidate_profile().table_definitions(catalog.sha256),
    )
    table = next(
        t for t in extraction.tables if t.definition.table_id == "WS06-R06-aggregate"
    )
    cells = {cell.coordinate: cell for cell in table.cells}
    axes = (
        ("superannuation", "J"),
        ("ordinary_hours", "M"),
        ("average_penalties", "S"),
        ("public_holiday_penalty", "V"),
        ("private_practice_loading", "Y"),
        ("retention_allowance", "AB"),
        ("sick_leave", "AE"),
        ("professional_development", "AH"),
        ("annual_leave", "AK"),
        ("salary", "AR"),
    )
    for row in range(34, 39):
        assert_that(cells[f"A{row}"].source.value == "ALL")
        for group, (name, first_input) in enumerate(axes):
            for offset, bound in enumerate(("lower", "midpoint", "upper")):
                annual_column = get_column_letter(53 + 6 * group + offset)
                hourly_column = get_column_letter(56 + 6 * group + offset)
                annual = cells[f"{annual_column}{row}"]
                hourly = cells[f"{hourly_column}{row}"]
                assert_that(annual.column_name == f"{name}_{bound}_annual_cost")
                assert_that(hourly.column_name == f"{name}_{bound}_hourly_cost")
                assert_that(annual.unit == "AUD/year" and hourly.unit == "AUD/hour")
                assert_that(
                    annual.role == hourly.role == "archived_sensitivity_scenario",
                )
                if name != "ordinary_hours":
                    axis_col = get_column_letter(
                        column_index_from_string(first_input) + offset,
                    )
                    assert_that(
                        re.search(
                            rf"(?<![A-Z0-9_]){axis_col}{row}(?![0-9])",
                            str(annual.source.value).replace("$", ""),
                        )
                        is not None,
                    )
                divisor = ("O", "N", "M")[offset] if name == "ordinary_hours" else "N"
                assert_that(
                    str(hourly.source.value).replace("$", "")
                    == f"={annual_column}{row}/52/{divisor}{row}",
                )
    assert_that("AK34" not in cells)
    assert_that(cells["AK35"].source.value == 0)
    assert_that(cells["AK35"].column_name == "annual_leave_lower")

    display = next(
        t for t in extraction.tables if t.definition.table_id == "WS06-R06-formatted"
    )
    labels = {cell.coordinate: cell for cell in display.cells}
    for row in range(40, 45):
        for column, unit in (("DC", "cost"), ("DF", "hourly")):
            cell = labels[f"{column}{row}"]
            assert_that(
                cell.column_name == f"salary_{unit}_lower_midpoint_upper_display",
            )
            assert_that(cell.role == "presentation")

    for table_id, axis, rows in (
        ("WS07-R01-leave_loading", "leave_loading", range(4, 29)),
        ("WS07-R01-summary_salary", "salary", range(29, 34)),
    ):
        table = next(t for t in extraction.tables if t.definition.table_id == table_id)
        values = [cell for cell in table.cells if cell.source.row in rows]
        assert_that(len(values) == 6 * len(rows))
        assert_that(
            all((cell.column_name or "").startswith(f"{axis}_") for cell in values),
        )
