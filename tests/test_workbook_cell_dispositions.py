# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Synthetic cell-level regressions for workbook label and metadata dispositions."""

lazy from collections.abc import Mapping
lazy from pathlib import Path

from openpyxl import Workbook

from src.workbook_catalog import read_workbook_catalog
from src.workbook_profile import load_candidate_profile
from src.workbook_tables import TableCell, extract_tables
from tests.checks import assert_that


def miniature(
    tmp_path: Path,
    identity: str,
    values: Mapping[str, str | int],
) -> dict[str, TableCell]:
    """Exercise one coordinate definition without applying a full pinned profile."""
    table = next(
        t for t in load_candidate_profile().definitions if t.table_id == identity
    )
    book = Workbook()
    sheet = book.active
    if sheet is None:
        msg = "Synthetic workbook requires its default sheet"
        raise ValueError(msg)
    sheet.title = table.sheet
    for coordinate, value in values.items():
        sheet[coordinate] = value
    path = tmp_path / "miniature.xlsx"
    book.save(path)
    book.close()
    extracted = extract_tables(read_workbook_catalog(path), (table.definition(),))
    return {c.coordinate: c for c in extracted.tables[0].cells}


def test_input_metadata_preserves_aliases_notes_and_unparsed_pay_text(
    tmp_path: Path,
) -> None:
    """Labels and source descriptions must not masquerade as accepted prices."""
    values = {
        "A4": "Synthetic jurisdiction",
        "B4": "Synthetic occupation",
        "C4": "Opaque label",
        "D4": "Unresolved instrument alias",
        "E4": "Unverified grade text",
        "F4": "Uncalibrated distribution note",
        "G4": "Unverified citation",
        "H4": "Mixed basis description",
        "I4": 2099,
    }
    cells = miniature(tmp_path, "WS01-R01-inputs", values)
    assert_that(cells["A4"].role == "identity")
    assert_that(cells["B4"].role == "identity")
    assert_that(cells["D4"].role == "source_reference")
    assert_that(cells["F4"].role == "assumption_note")
    assert_that(cells["H4"].unit is None)
    assert_that(cells["H4"].role == "source_description")
    assert_that(cells["I4"].unit == "year")
    for coordinate, value in values.items():
        assert_that(cells[coordinate].source.value == value)
        assert_that(cells[coordinate].role is not None)


def test_dsa_identity_order_is_explicit(tmp_path: Path) -> None:
    """Long-form DSA uses personnel, jurisdiction and scenario in that order."""
    cells = miniature(
        tmp_path,
        "WS08-R01",
        {"A3": "Synthetic role", "B3": "Synthetic place", "C3": "Scenario"},
    )
    expected = {
        "A3": "personnel_type",
        "B3": "jurisdiction",
        "C3": "scenario_name",
    }
    for coordinate, name in expected.items():
        assert_that(cells[coordinate].column_name == name)
        assert_that(cells[coordinate].role == "identity")
        assert_that(cells[coordinate].unit is None)


def test_standalone_unit_heading_is_not_a_jurisdiction(tmp_path: Path) -> None:
    """An inline currency heading stays a header above the following identities."""
    cells = miniature(
        tmp_path,
        "WS01-R08",
        {"A46": "$", "A47": "Synthetic place", "B47": "Synthetic role"},
    )
    assert_that(cells["A46"].role is None)
    assert_that(cells["A46"].column_name is None)
    assert_that(cells["A47"].column_name == "jurisdiction_or_aggregate")
    assert_that(cells["A47"].role == "identity")


def test_medicare_measure_labels_have_no_quantity_unit(tmp_path: Path) -> None:
    """Preserve a measure label separately from the adjacent count."""
    cells = miniature(
        tmp_path,
        "WS03-R02-total_cards",
        {"A18": "Synthetic measure", "B18": 3},
    )
    assert_that(cells["A18"].role == "label")
    assert_that(cells["A18"].unit is None)
    assert_that(cells["B18"].unit is not None)


def test_dsa_reported_year_remains_a_historical_label(tmp_path: Path) -> None:
    """A recorded year is not silently converted to an operative date."""
    value = 2099
    cells = miniature(tmp_path, "WS06-R01-inputs", {"I4": value})
    assert_that(cells["I4"].column_name == "reported_year")
    assert_that(cells["I4"].role == "historical_reference")
    assert_that(cells["I4"].unit == "year")
    assert_that(cells["I4"].source.value == value)
