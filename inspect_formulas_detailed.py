# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Inspect the original workforce workbook formulas locally."""

import sys
from pathlib import Path

import openpyxl


def inspect_excel_formulas_detailed() -> None:
    """Inspect salary and total-cost formulas for selected workforce rows."""
    file_path = Path("data") / "Labour Model - v3, 20240328.xlsx"
    personnel_types_to_check = {
        "Lab technician",
        "Medical scientist",
        "Admin staff",
        "Bioinformatics staff",
        "Pathologists",
    }

    try:
        workbook = openpyxl.load_workbook(file_path, data_only=False)
        sheet = workbook["Labour - Prices"]

        sys.stdout.write(
            "--- Detailed Formula Inspection in 'Labour - Prices' Sheet ---" + "\n",
        )

        # Columns:
        # B (2): Personnel Type
        # S (19), T (20), U (21): Base Salary (LL, Mid, UL)
        # V (22), W (23), X (24): Base Salary + Costs (LL, Mid, UL)

        found_personnel = set()

        for row_index in range(4, sheet.max_row + 1):
            personnel_type = sheet.cell(row=row_index, column=2).value

            if (
                personnel_type in personnel_types_to_check
                and personnel_type not in found_personnel
            ):
                sys.stdout.write(
                    str(f"\nPersonnel Type: {personnel_type} (Row {row_index})") + "\n",
                )

                # Base Salary Formulas
                formula_s = sheet.cell(row=row_index, column=19).value
                formula_t = sheet.cell(row=row_index, column=20).value
                formula_u = sheet.cell(row=row_index, column=21).value
                sys.stdout.write("  Base Salary Formulas:" + "\n")
                sys.stdout.write(str(f"    Col S (LL): {formula_s}") + "\n")
                sys.stdout.write(str(f"    Col T (Mid): {formula_t}") + "\n")
                sys.stdout.write(str(f"    Col U (UL): {formula_u}") + "\n")

                # Base Salary + Costs Formulas
                formula_v = sheet.cell(row=row_index, column=22).value
                formula_w = sheet.cell(row=row_index, column=23).value
                formula_x = sheet.cell(row=row_index, column=24).value
                sys.stdout.write("  Base Salary + Costs Formulas:" + "\n")
                sys.stdout.write(str(f"    Col V (LL): {formula_v}") + "\n")
                sys.stdout.write(str(f"    Col W (Mid): {formula_w}") + "\n")
                sys.stdout.write(str(f"    Col X (UL): {formula_x}") + "\n")

                found_personnel.add(personnel_type)

            if len(found_personnel) == len(personnel_types_to_check):
                break

    except FileNotFoundError:
        sys.stdout.write(str(f"Error: File not found at {file_path}") + "\n")


if __name__ == "__main__":
    inspect_excel_formulas_detailed()
