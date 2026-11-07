# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Lossless, read-only workbook intake before any economic interpretation."""

import json
from dataclasses import dataclass
from datetime import date, datetime, time
from hashlib import sha256
from typing import TYPE_CHECKING
lazy from pathlib import Path

import openpyxl
import polars as pl
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.formula import ArrayFormula

if TYPE_CHECKING:
    from openpyxl.worksheet.worksheet import Worksheet

type Scalar = str | int | float | bool | date | datetime | time | None


@dataclass(frozen=True)
class CellRecord:
    """Preserve a populated source cell, its raw type and optional cached value."""

    coordinate: str
    row: int
    column: int
    value: Scalar
    cached: Scalar
    excel_type: str
    cached_type: str
    number_format: str
    hyperlink: str | None
    array_formula_range: str | None = None


@dataclass(frozen=True)
class SheetCatalog:
    """Account for cells, physical regions and structural worksheet metadata."""

    name: str
    state: str
    dimension: str
    cells: tuple[CellRecord, ...]
    regions: tuple[str, ...]
    merged_ranges: tuple[str, ...]
    defined_names: dict[str, str]
    tables: dict[str, str]


@dataclass(frozen=True)
class WorkbookCatalog:
    """Keep every worksheet while leaving source acceptance explicit."""

    sha256: str
    sheets: tuple[SheetCatalog, ...]
    defined_names: dict[str, str]

    def cells_frame(self) -> pl.DataFrame:
        """Return typed coordinates and lossless JSON scalar representations."""
        schema = {
            "sheet": pl.String,
            "coordinate": pl.String,
            "row": pl.Int64,
            "column": pl.Int64,
            "value_json": pl.String,
            "cached_json": pl.String,
            "excel_type": pl.String,
            "value_kind": pl.String,
            "cached_type": pl.String,
            "cached_kind": pl.String,
            "number_format": pl.String,
            "hyperlink": pl.String,
            "array_formula_range": pl.String,
        }
        return pl.DataFrame(
            [
                {
                    "sheet": s.name,
                    "coordinate": c.coordinate,
                    "row": c.row,
                    "column": c.column,
                    "value_json": json.dumps(c.value, default=str),
                    "cached_json": json.dumps(c.cached, default=str),
                    "excel_type": c.excel_type,
                    "value_kind": type(c.value).__name__,
                    "cached_type": c.cached_type,
                    "cached_kind": type(c.cached).__name__,
                    "number_format": c.number_format,
                    "hyperlink": c.hyperlink,
                    "array_formula_range": c.array_formula_range,
                }
                for s in self.sheets
                for c in s.cells
            ],
            schema=schema,
        )

    def manifest(self) -> dict[str, object]:
        """Expose intake coverage without embedding real-world parameter values."""
        return {
            "schema_version": 1,
            "sha256": self.sha256,
            "defined_names": self.defined_names,
            "sheets": [
                {
                    "name": s.name,
                    "state": s.state,
                    "dimension": s.dimension,
                    "cells": len(s.cells),
                    "regions": s.regions,
                    "formulas": sum(c.excel_type == "f" for c in s.cells),
                    "missing_formula_caches": sum(
                        c.excel_type == "f" and c.cached is None for c in s.cells
                    ),
                    "defined_names": s.defined_names,
                    "tables": s.tables,
                    "merged_ranges": s.merged_ranges,
                    "status": "empty" if not s.cells else "raw_intake_only",
                }
                for s in self.sheets
            ],
        }


def _scalar(value: object) -> Scalar:
    if value is None or isinstance(value, (str, int, float, date, time)):
        return value
    message = "Unsupported workbook cell object; preserve through an explicit adapter"
    raise ValueError(message)


def _regions(cells: tuple[CellRecord, ...]) -> tuple[str, ...]:
    groups: list[list[int]] = []
    for row in sorted({c.row for c in cells}):
        if groups and row == groups[-1][-1] + 1:
            groups[-1].append(row)
        else:
            groups.append([row])
    result: list[str] = []
    for group in groups:
        subset = [c for c in cells if group[0] <= c.row <= group[-1]]
        low = get_column_letter(min(c.column for c in subset))
        high = get_column_letter(max(c.column for c in subset))
        result.append(f"{low}{group[0]}:{high}{group[-1]}")
    return tuple(result)


def _sheet(sheet: Worksheet, cached: Worksheet) -> SheetCatalog:
    cells = tuple(
        CellRecord(
            cell.coordinate,
            cell.row,
            cell.column,
            _scalar(
                cell.value.text if isinstance(cell.value, ArrayFormula) else cell.value,
            ),
            _scalar(cached[cell.coordinate].value),
            cell.data_type,
            cached[cell.coordinate].data_type,
            cell.number_format,
            cell.hyperlink.target or cell.hyperlink.location
            if cell.hyperlink
            else None,
            cell.value.ref if isinstance(cell.value, ArrayFormula) else None,
        )
        for row in sheet
        for cell in row
        if cell.value is not None
    )
    return SheetCatalog(
        sheet.title,
        sheet.sheet_state,
        sheet.calculate_dimension(),
        cells,
        _regions(cells),
        tuple(str(r) for r in sheet.merged_cells.ranges),
        {key: str(value.attr_text) for key, value in sheet.defined_names.items()},
        {table.name: table.ref for table in sheet.tables.values()},
    )


def read_workbook_catalog(
    path: Path,
    *,
    sheet_names: tuple[str, ...] | None = None,
) -> WorkbookCatalog:
    """Read all or explicitly selected sheets without modifying the source."""
    digest = sha256(path.read_bytes()).hexdigest()
    # Normal mode gives constant-time cache lookup; read-only indexed lookup rescans.
    book = openpyxl.load_workbook(path, data_only=False)
    cached = openpyxl.load_workbook(path, data_only=True)
    try:
        selected = book.worksheets
        if sheet_names is not None:
            requested = set(sheet_names)
            if requested - set(book.sheetnames) or len(requested) != len(sheet_names):
                msg = "Workbook sheet selection must contain known, unique names"
                raise ValueError(msg)
            selected = [sheet for sheet in selected if sheet.title in requested]
        result = WorkbookCatalog(
            digest,
            tuple(_sheet(sheet, cached[sheet.title]) for sheet in selected),
            {key: str(value.attr_text) for key, value in book.defined_names.items()},
        )
    finally:
        book.close()
        cached.close()
    if sha256(path.read_bytes()).hexdigest() != digest:
        message = "Workbook changed during intake"
        raise ValueError(message)
    return result
