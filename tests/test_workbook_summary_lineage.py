# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Reconcile historical component summary, transposition and source lineage."""

from decimal import Decimal
from hashlib import sha256
from pathlib import Path

from openpyxl import load_workbook

from tests.checks import assert_that


def test_summary_preserves_five_state_means_and_transposed_cells() -> None:
    """Trace 55 historical values and five display ranges without accepting them."""
    path = Path("data/Labour Model - v3, 20240328.xlsx")
    expected_hash = "c72a5f9d8a232ee559516978537a7efdd1aea6df55738e9d851840fff837ddca"
    assert_that(sha256(path.read_bytes()).hexdigest() == expected_hash)
    workbook = load_workbook(path, read_only=True, data_only=False)
    try:
        source = workbook["Labour - Prices"]
        summary = workbook["Sum Cost Comp"]
        for role_index in range(5):
            row = role_index + 3
            source_rows = [4 + role_index + 6 * n for n in range(5)]
            role = summary.cell(row, 1).value
            assert_that(summary.cell(9, role_index + 2).value == role)
            assert_that(all(source.cell(r, 2).value == role for r in source_rows))
            for field, column in enumerate("JKMNOPQRSTU"):
                original = summary.cell(row, field + 2).value
                transposed = summary.cell(field + 10, role_index + 2).value
                assert_that(original == transposed)
                assert_that(
                    summary.cell(2, field + 2).value
                    == summary.cell(field + 10, 1).value,
                )
                values = [source[f"{column}{r}"].value for r in source_rows]
                amounts = [
                    Decimal(4) if v == "=160/40" else Decimal(str(v)) for v in values
                ]
                assert_that(Decimal(str(original)) == sum(amounts, Decimal(0)) / 5)
                refs = ",".join(f"{column}{r}" for r in reversed(source_rows))
                assert_that(
                    source[f"{column}{34 + role_index}"].value == f"=AVERAGE({refs})",
                )
            assert_that(
                summary.cell(row, 13).value == summary.cell(21, role_index + 2).value,
            )
    finally:
        workbook.close()
    assert_that(sha256(path.read_bytes()).hexdigest() == expected_hash)
