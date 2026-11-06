# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Aggregate input semantics follow formulas rather than the WM sheet label."""

from pathlib import Path

from openpyxl.utils import get_column_letter

from src.workbook_catalog import read_workbook_catalog
from src.workbook_profile import load_candidate_profile
from src.workbook_tables import extract_tables
from tests.checks import assert_that


def test_aggregate_inputs_and_display_preserve_unweighted_bases() -> None:
    """Trace all 240 mean/display formulas across the two sheets."""
    catalog = read_workbook_catalog(Path("data/Labour Model - v3, 20240328.xlsx"))
    extraction = extract_tables(
        catalog,
        load_candidate_profile().table_definitions(catalog.sha256),
    )
    tables = {t.definition.table_id: t for t in extraction.tables}
    for prefix in ("WS01", "WS02"):
        inputs = tables[f"{prefix}-R06-aggregate-inputs"]
        display = tables[f"{prefix}-R07-formatted-inputs"]
        numeric = {c.coordinate: c for c in inputs.cells}
        formatted = {c.coordinate: c for c in display.cells}
        for offset in range(5):
            row = 34 + offset
            for index in range(10, 22):
                col = get_column_letter(index)
                refs = ",".join(f"{col}{r + offset}" for r in (28, 22, 16, 10, 4))
                cell = numeric[f"{col}{row}"]
                assert_that(cell.source.value == f"=AVERAGE({refs})")
                assert_that((cell.column_name or "").endswith("_unweighted_mean"))
                assert_that(cell.role == "archived_aggregate_input")
                shown = formatted[f"{col}{row + 6}"]
                style = "$0.0" if col == "R" else "0.0" if col in ("K", "S") else "0.0%"
                expected = (
                    f'=TEXT({col}{row}, "{style}") & " (" & '
                    f'TEXT(MIN({refs}), "{style}") & " - " & '
                    f'TEXT(MAX({refs}), "{style}") & ")"'
                )
                assert_that(shown.source.value == expected)
                assert_that(shown.unit == "text" and shown.role == "presentation")
