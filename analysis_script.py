# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Inspect workbook headers locally."""

import sys
from itertools import islice

import openpyxl


def inspect_raw_headers(file_path: str, sheet_name: str) -> None:
    """Report the first ten workbook rows without modifying the source."""
    book = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    try:
        for row in islice(book[sheet_name].values, 10):
            sys.stdout.write(str(row) + "\n")
    finally:
        book.close()


if __name__ == "__main__":
    from src import config
    from src.data_loader import load_and_clean_data

    sys.stdout.write(
        str(
            load_and_clean_data(
                config.DATA_FILE_PATH,
                config.LABOUR_PRICES_SHEET,
            ).head(),
        )
        + "\n",
    )
