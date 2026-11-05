# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Recalculate original workbook copies with each declared scenario's inputs."""

import tempfile
from pathlib import Path
from typing import Any

import openpyxl
import polars as pl

from src import config as workbook_config
from src.libreoffice import recalculate
from src.numeric import row_filter


def compare_scenarios(
    source: Path,
    scenarios: list[tuple[str, pl.DataFrame, dict[str, Any], dict[str, str]]],
    baseline: dict[tuple[str, str], dict[str, Any]],
) -> pl.DataFrame:
    """Recalculate original workbook copies and compare every state-role cost."""
    checks: list[dict[str, str | int | float | bool]] = []
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        target = root / "recalculated"
        target.mkdir()
        files: list[Path] = []
        for i, (_name, _changed, config, mapping) in enumerate(scenarios):
            book = openpyxl.load_workbook(source)
            sheet = book["Labour - Prices"]
            headers = {f"Grade(s)_{sheet.cell(3, c).value}": c for c in range(10, 22)}
            for param, variation in zip(
                config.get("parameters_to_vary", [config.get("parameter_to_vary")]),
                config.get("variations", [config.get("variation")]),
                strict=True,
            ):
                column = headers[mapping[param]]
                for row in range(4, 33):
                    keys = {
                        "Jurisdiction": sheet.cell(row, 1).value,
                        "Personnel type": sheet.cell(row, 2).value,
                    }
                    if not all(keys.values()) or any(
                        keys[k] != v
                        for k, v in row_filter(config.get("row_filter")).items()
                    ):
                        continue
                    cell = sheet.cell(row, column)
                    old = baseline[
                        (str(keys["Jurisdiction"]), str(keys["Personnel type"]))
                    ][mapping[param]]
                    cell.value = (
                        old * (1 + variation["value"])
                        if variation["type"] == "percentage"
                        else old + variation["value"]
                    )
            path = root / f"{i}.xlsx"
            book.save(path)
            book.close()
            files.append(path)
        recalculate(files, target, root / "profile")
        for file, (name, changed, _, _) in zip(files, scenarios, strict=True):
            book = openpyxl.load_workbook(
                target / file.name,
                read_only=True,
                data_only=True,
            )
            rows = list(book["Labour - Prices"].values)
            book.close()
            expected = {(r[0], r[1]): r[25] for r in rows[3:32] if r[0] and r[1]}
            join_keys = ["Jurisdiction", "Personnel type"]
            if (
                len(expected) != workbook_config.EXPECTED_STATE_ROLE_ROWS
                or changed.height != workbook_config.EXPECTED_STATE_ROLE_ROWS
                or changed.select(join_keys).is_duplicated().any()
            ):
                message = "Expected 25 unique state-role comparisons"
                raise ValueError(message)
            diffs = [
                abs(
                    r["Calculated_Cost_Mid_Y0"]
                    - expected[(r[join_keys[0]], r[join_keys[1]])],
                )
                for r in changed.iter_rows(named=True)
            ]
            checks.append(
                {
                    "scenario": name,
                    "comparisons": len(diffs),
                    "maximum_difference": max(diffs),
                    "within_cent": max(diffs) < workbook_config.PARITY_TOLERANCE,
                },
            )
    return pl.DataFrame(checks)
