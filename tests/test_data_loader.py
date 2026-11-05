# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Verify original workbook identity rows and positive reference costs."""

from src import config
from src.data_loader import load_and_clean_data, load_dsa_validation_data
from src.numeric import numeric
from tests.checks import assert_that

EXPECTED_25 = 25


def test_load_and_clean_data() -> None:
    """Retain the complete, uniquely identified workforce input table."""
    frame = load_and_clean_data(config.DATA_FILE_PATH, config.LABOUR_PRICES_SHEET)
    assert_that(frame.height == EXPECTED_25)
    assert_that(
        frame.select("Jurisdiction", "Personnel type").unique().height == EXPECTED_25,
    )
    assert_that(frame["Personnel type"].null_count() == 0)
    assert_that(numeric(frame["Base Salary_Mid-point"].min()) > 0)


def test_load_dsa_validation_data() -> None:
    """Retain every archived workforce validation row and its reference costs."""
    frame = load_dsa_validation_data(config.DATA_FILE_PATH, config.DSA_VALIDATION_SHEET)
    assert_that(frame.height == EXPECTED_25)
    assert_that(
        frame.select("Jurisdiction", "Personnel type").unique().height == EXPECTED_25,
    )
    assert_that(frame["Personnel type"].null_count() == 0)
    assert_that(numeric(frame["Superannuation Rate_Base Salary + Costs_MP"].min()) > 0)
