# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
# tests/test_formula_engine.py
"""Test for the formula_engine module."""

import json
from typing import Any
from unittest.mock import mock_open, patch

import polars as pl
import pytest
from polars import DataFrame
from polars.testing import assert_series_equal
lazy from _pytest.logging import LogCaptureFixture

from src.formula_engine import apply_formulas, load_formulas
from tests.checks import assert_that

# --- Tests for load_formulas ---


def test_load_formulas_success() -> None:
    """Test successful loading of a valid formula file."""
    mock_content = {
        "formulas": [{"id": "test_formula", "expression": "a + b"}],
        "outputs": [{"name": "test_output", "calculation_method": "formula"}],
    }
    mock_json = json.dumps(mock_content)
    with patch("pathlib.Path.open", mock_open(read_data=mock_json)) as mock_file:
        formulas = load_formulas("dummy/path.json")
        assert_that(formulas == mock_content)
        mock_file.assert_called_once_with()


def test_load_formulas_file_not_found() -> None:
    """Test that FileNotFoundError is raised for a missing file."""
    with pytest.raises(FileNotFoundError):
        load_formulas("non_existent_file.json")


def test_load_formulas_invalid_json() -> None:
    """Test that ValueError is raised for a malformed JSON file."""
    with (
        patch("pathlib.Path.open", mock_open(read_data="{invalid json")),
        pytest.raises(ValueError, match="Invalid JSON format"),
    ):
        load_formulas("dummy/path.json")


@pytest.mark.parametrize(
    "bad_content",
    [
        {"outputs": []},  # Missing 'formulas'
        {"formulas": []},  # Missing 'outputs'
    ],
)
def test_load_formulas_missing_keys(bad_content: dict[str, Any]) -> None:
    """Test that ValueError is raised if required keys are missing."""
    mock_json = json.dumps(bad_content)
    with (
        patch("pathlib.Path.open", mock_open(read_data=mock_json)),
        pytest.raises(ValueError, match="missing required keys"),
    ):
        load_formulas("dummy/path.json")


# --- Tests for apply_formulas ---


@pytest.fixture
def sample_data_frame() -> DataFrame:
    """Provide a sample DataFrame for testing."""
    return pl.DataFrame({"col_a": [10, 20], "col_b": [2, 4]})


@pytest.fixture
def sample_formulas() -> dict[str, Any]:
    """Provide a sample formula definition for testing."""
    return {
        "formulas": [
            {
                "id": "dependency_1",
                "expression": "col_a / 2",
                "parameters": ["col_a"],
            },
            {
                "id": "main_formula",
                "expression": "dependency_1 * col_b",
                "dependencies": ["dependency_1"],
                "parameters": ["dependency_1", "col_b"],
            },
        ],
        "outputs": [
            {
                "name": "Calculated_Cost",
                "calculation_method": "formula",
                "uses_formula": "main_formula",
                "parameter_mapping": {
                    "col_a": "col_a",
                    "col_b": "col_b",
                    "dependency_1": "dependency_1",
                },
            },
            {
                "name": "Direct_Cost",
                "calculation_method": "direct",
                "source_column": "col_a",
            },
        ],
    }


def test_apply_formulas_e2e(
    sample_data_frame: DataFrame,
    sample_formulas: dict[str, Any],
) -> None:
    """Test the end-to-end application of formulas."""
    result_df = apply_formulas(sample_data_frame, sample_formulas)

    # Check direct calculation
    assert_that("Direct_Cost_Y0" in result_df.columns)
    assert_series_equal(
        result_df["Direct_Cost_Y0"],
        sample_data_frame["col_a"],
        check_names=False,
    )

    # Check formula calculation
    # Row 1: (10 / 2) * 2 = 10
    # Row 2: (20 / 2) * 4 = 40
    expected_formula_result = pl.Series([10.0, 40.0])
    assert_that("Calculated_Cost_Y0" in result_df.columns)
    assert_series_equal(
        result_df["Calculated_Cost_Y0"],
        expected_formula_result,
        check_names=False,
    )


def test_apply_formulas_productive_time_warning(
    sample_data_frame: DataFrame,
    caplog: LogCaptureFixture,
) -> None:
    """Test that a warning is logged if productive_time_factor is zero."""
    formulas: dict[str, Any] = {
        "formulas": [
            {
                "id": "test_formula",
                "expression": "col_a / productive_time_factor",
                "parameters": ["col_a", "productive_time_factor"],
            },
        ],
        "outputs": [
            {
                "name": "Test",
                "calculation_method": "formula",
                "uses_formula": "test_formula",
                "parameter_mapping": {
                    "col_a": "col_a",
                    # This parameter is missing from the data, will default to 0
                    "productive_time_factor": "missing_col",
                },
            },
        ],
    }
    apply_formulas(sample_data_frame, formulas)
    assert_that("Productive time factor is 0" in caplog.text)
