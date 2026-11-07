# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Segment catalogued workbook cells using explicit, reviewable table definitions."""

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

from openpyxl.utils.cell import column_index_from_string, range_boundaries

if TYPE_CHECKING:
    from src.workbook_catalog import CellRecord, WorkbookCatalog


@dataclass(frozen=True)
class ColumnMeaning:
    """A reviewed column interpretation, never inferred from a display header."""

    column: str
    name: str
    unit: str | None
    role: str


@dataclass(frozen=True)
class TableDefinition:
    """One explicit rectangular table or unresolved physical region."""

    table_id: str
    sheet: str
    area: str
    status: str
    purpose: str
    columns: tuple[ColumnMeaning, ...] = ()
    header_rows: tuple[int, ...] = ()


@dataclass(frozen=True)
class TableCell:
    """One original cell and its declared column meaning, if reviewed."""

    source: CellRecord
    table_id: str
    column_name: str | None
    unit: str | None
    role: str | None

    @property
    def coordinate(self) -> str:
        """Return the unaltered workbook cell coordinate."""
        return self.source.coordinate


@dataclass(frozen=True)
class ExtractedTable:
    """An identified table retaining every assigned original cell."""

    definition: TableDefinition
    cells: tuple[TableCell, ...]


@dataclass(frozen=True)
class TableExtraction:
    """Reconciled extraction, including uncovered cells and empty sheets."""

    workbook_sha256: str
    tables: tuple[ExtractedTable, ...]
    unassigned: tuple[tuple[str, str], ...]
    empty_sheets: tuple[str, ...]


def _columns(
    definition: TableDefinition,
    min_col: int,
    max_col: int,
) -> dict[int, ColumnMeaning]:
    result: dict[int, ColumnMeaning] = {}
    for meaning in definition.columns:
        column = column_index_from_string(meaning.column)
        if column in result or not min_col <= column <= max_col:
            msg = "Table columns must be unique and inside the range"
            raise ValueError(msg)
        result[column] = meaning
    return result


def extract_tables(
    catalog: WorkbookCatalog,
    definitions: tuple[TableDefinition, ...],
) -> TableExtraction:
    """Assign populated cells once; preserve unknowns instead of inventing units."""
    sheets = {sheet.name: sheet for sheet in catalog.sheets}
    ids: set[str] = set()
    assigned: set[tuple[str, str]] = set()
    tables: list[ExtractedTable] = []
    for definition in definitions:
        if not definition.table_id or definition.table_id in ids:
            msg = "Table identities must be nonempty and unique"
            raise ValueError(msg)
        ids.add(definition.table_id)
        if definition.sheet not in sheets:
            msg = f"Unknown sheet in table definition: {definition.sheet}"
            raise ValueError(msg)
        min_col, min_row, max_col, max_row = range_boundaries(definition.area)
        if min_col is None or min_row is None or max_col is None or max_row is None:
            msg = "Table range must have explicit finite bounds"
            raise ValueError(msg)
        column_map = _columns(definition, min_col, max_col)
        cells: list[TableCell] = []
        for cell in sheets[definition.sheet].cells:
            if min_row <= cell.row <= max_row and min_col <= cell.column <= max_col:
                key = (definition.sheet, cell.coordinate)
                if key in assigned:
                    msg = f"Table definitions overlap at {key}"
                    raise ValueError(msg)
                assigned.add(key)
                meaning = column_map.get(cell.column)
                # Header rows are descriptions, not values with a monetary unit.
                if cell.row in definition.header_rows:
                    meaning = None
                cells.append(
                    TableCell(
                        cell,
                        definition.table_id,
                        meaning.name if meaning else None,
                        meaning.unit if meaning else None,
                        meaning.role if meaning else None,
                    ),
                )
        if not cells:
            msg = f"Table definition has no populated cells: {definition.table_id}"
            raise ValueError(msg)
        tables.append(ExtractedTable(definition, tuple(cells)))
    unassigned = tuple(
        (sheet.name, cell.coordinate)
        for sheet in catalog.sheets
        for cell in sheet.cells
        if (sheet.name, cell.coordinate) not in assigned
    )
    return TableExtraction(
        catalog.sha256,
        tuple(tables),
        unassigned,
        tuple(sheet.name for sheet in catalog.sheets if not sheet.cells),
    )


def extract_vehicle_opening_amounts(
    catalog: WorkbookCatalog,
) -> dict[str, Decimal | None]:
    """Read the Queensland template's core vehicle lookup using cached keys.

    A present key with no opening amount remains None. Unknown keys remain
    absent from the mapping. An uncalculated or erroneous key is invalid.
    """
    (table,) = extract_tables(
        catalog,
        (
            TableDefinition(
                "qld-vehicle-opening",
                "MV Allowance",
                "C2:D25",
                "reviewed",
                "Core vehicle lookup keys and opening annual budget amounts",
            ),
        ),
    ).tables
    cells = {(cell.source.row, cell.source.column): cell.source for cell in table.cells}
    amounts: dict[str, Decimal | None] = {}
    for row in range(2, 26):
        key_cell = cells.get((row, 3))
        key = key_cell.cached if key_cell and key_cell.cached_type != "e" else None
        if not isinstance(key, str) or not key.strip() or key in amounts:
            msg = f"Missing, invalid or duplicate vehicle lookup key at C{row}"
            raise ValueError(msg)
        amount = cells.get((row, 4))
        if amount is None:
            amounts[key] = None
            continue
        if type(amount.cached) not in (int, float):
            msg = f"Invalid vehicle opening amount at D{row}"
            raise ValueError(msg)
        value = Decimal(str(amount.cached))
        if not value.is_finite() or value < 0:
            msg = f"Invalid vehicle opening amount at D{row}"
            raise ValueError(msg)
        amounts[key] = value
    return amounts
