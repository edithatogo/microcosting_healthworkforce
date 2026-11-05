# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""List sheets in a selected local workbook."""

import sys

import openpyxl


def list_excel_sheets(file_path: str) -> None:
    """List all the sheet names in an Excel file."""
    workbook = openpyxl.load_workbook(file_path, read_only=True)
    sys.stdout.write("Sheet names:" + "\n")
    for sheet_name in workbook.sheetnames:
        sys.stdout.write(str(f"- {sheet_name}") + "\n")


if __name__ == "__main__":
    list_excel_sheets("data/Labour Model - v3, 20240328.xlsx")
