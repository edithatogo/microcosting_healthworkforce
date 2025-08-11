# tests/test_formula_engine.py
"""
Tests for the formula_engine module.
"""

import json
from typing import Any, Dict
from unittest.mock import mock_open, patch

import pandas as pd
import pytest
from _pytest.logging import LogCaptureFixture
from pandas import DataFrame

from src.formula_engine import apply_formulas, load_formulas

# --- Tests for load_formulas ---


def test_load_formulas_success() -> None:
    """Tests successful loading of a valid formula file."""
    mock_content = {
        "formulas": [{"id": "test_formula", "expression": "a + b"}],
        "outputs": [{"name": "test_output", "calculation_method": "formula"}],
    }
    mock_json = json.dumps(mock_content)
    with patch("builtins.open", mock_open(read_data=mock_json)) as mock_file:
        formulas = load_formulas("dummy/path.json")
        assert formulas == mock_content
        mock_file.assert_called_once_with("dummy/path.json", "r")


def test_load_formulas_file_not_found() -> None:
    """Tests that FileNotFoundError is raised for a missing file."""
    with pytest.raises(FileNotFoundError):
        load_formulas("non_existent_file.json")


def test_load_formulas_invalid_json() -> None:
    """Tests that ValueError is raised for a malformed JSON file."""
    with patch("builtins.open", mock_open(read_data="{invalid json")):
        with pytest.raises(ValueError, match="Invalid JSON format"):
            load_formulas("dummy/path.json")


@pytest.mark.parametrize(  # type: ignore[misc]
    "bad_content",
    [
        {"outputs": []},  # Missing 'formulas'
        {"formulas": []},  # Missing 'outputs'
    ],
)
def test_load_formulas_missing_keys(bad_content: Dict[str, Any]) -> None:
    """Tests that ValueError is raised if required keys are missing."""
    mock_json = json.dumps(bad_content)
    with patch("builtins.open", mock_open(read_data=mock_json)):
        with pytest.raises(ValueError, match="missing required keys"):
            load_formulas("dummy/path.json")


# --- Tests for apply_formulas ---


@pytest.fixture  # type: ignore[misc]
def sample_data_frame() -> DataFrame:
    """Provides a sample DataFrame for testing."""
    return pd.DataFrame({"col_a": [10, 20], "col_b": [2, 4]})


@pytest.fixture  # type: ignore[misc]
def sample_formulas() -> Dict[str, Any]:
    """Provides a sample formula definition for testing."""
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
    sample_data_frame: DataFrame, sample_formulas: Dict[str, Any]
) -> None:
    """Tests the end-to-end application of formulas."""
    result_df = apply_formulas(sample_data_frame, sample_formulas)

    # Check direct calculation
    assert "Direct_Cost_Y0" in result_df.columns
    pd.testing.assert_series_equal(
        result_df["Direct_Cost_Y0"],
        sample_data_frame["col_a"],
        check_names=False,
    )

    # Check formula calculation
    # Row 1: (10 / 2) * 2 = 10
    # Row 2: (20 / 2) * 4 = 40
    expected_formula_result = pd.Series([10.0, 40.0])
    assert "Calculated_Cost_Y0" in result_df.columns
    pd.testing.assert_series_equal(
        result_df["Calculated_Cost_Y0"],
        expected_formula_result,
        check_names=False,
    )


def test_apply_formulas_productive_time_warning(
    sample_data_frame: DataFrame, caplog: LogCaptureFixture
) -> None:
    """Tests that a warning is logged if productive_time_factor is zero."""
    formulas: Dict[str, Any] = {
        "formulas": [
            {
                "id": "test_formula",
                "expression": "col_a / productive_time_factor",
                "parameters": ["col_a", "productive_time_factor"],
            }
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
            }
        ],
    }
    apply_formulas(sample_data_frame, formulas)
    assert "Productive time factor is 0" in caplog.text
