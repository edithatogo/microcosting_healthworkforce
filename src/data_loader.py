# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Read delivered workforce tables with their original merged header levels."""

import tempfile
from pathlib import Path

import openpyxl
import polars as pl

from src import config
from src.libreoffice import recalculate
from src.workbook_run import parameters

IDENTITY_COLUMN_COUNT = 2


def _table(file_path: str, sheet_name: str, skip: int, levels: int) -> pl.DataFrame:
    book = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    try:
        rows = iter(book[sheet_name].values)
        for _ in range(skip):
            next(rows)
        headers = [list(next(rows)) for _ in range(levels)]
        names: list[str] = []
        counts: dict[str, int] = {}
        for i in range(len(headers[0])):
            parts: list[str] = []
            for level, row in enumerate(headers):
                value = row[i]
                if value is None and level < levels - 1 and i >= IDENTITY_COLUMN_COUNT:
                    value = next((v for v in reversed(row[:i]) if v is not None), None)
                if value is not None:
                    parts.append(str(value).strip())
            label = "_".join(parts) or f"column_{i}"
            n = counts.get(label, 0)
            names.append(label if n == 0 else f"{label}.{n}")
            counts[label] = n + 1
        return pl.DataFrame(
            [[str(v) if v is not None else None for v in r] for r in rows],
            schema=dict.fromkeys(names, pl.String),
            orient="row",
        )
    finally:
        book.close()


def load_and_clean_data(file_path: str, sheet_name: str) -> pl.DataFrame:
    """Recalculate the original workbook and return validated workforce inputs."""
    if sheet_name != config.LABOUR_PRICES_SHEET:
        message = f"Unsupported primary sheet {sheet_name}"
        raise ValueError(message)
    source = Path(file_path).resolve()
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        recalculate([source], root, root / "profile")
        book = openpyxl.load_workbook(
            root / source.name,
            read_only=True,
            data_only=True,
        )
        try:
            return parameters(book)
        finally:
            book.close()


def load_dsa_validation_data(file_path: str, sheet_name: str) -> pl.DataFrame:
    """Read archived jurisdiction/role DSA values without manufacturing rows."""
    frame = _table(file_path, sheet_name, 0, 3)
    return frame.filter(
        pl.col("Jurisdiction").is_in(["VIC", "QLD", "NSW", "SA", "WA"]),
    ).with_columns(
        pl.exclude("Jurisdiction", "Personnel type").cast(pl.Float64, strict=False),
    )


def load_psa_validation_data(file_path: str, sheet_name: str) -> pl.DataFrame:
    """Read archived simulation summaries and preserve missing means."""
    frame = _table(file_path, sheet_name, 0, 1)
    return (
        frame.with_columns(pl.col("Expected Mean Cost").cast(pl.Float64, strict=False))
        if "Expected Mean Cost" in frame.columns
        else frame
    )
