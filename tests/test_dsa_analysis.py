# tests/test_dsa_analysis.py
"""
Tests for the dsa_analysis module.
"""

import logging
from typing import Any, Dict
from unittest.mock import mock_open, patch

import pandas as pd
import pytest
from _pytest.logging import LogCaptureFixture

from src.dsa_analysis import (
    load_dsa_scenarios,
    report_dsa_results,
    run_dsa_analysis,
)


def test_load_dsa_scenarios_success() -> None:
    """
    Tests that the load_dsa_scenarios function loads scenarios correctly from a
    JSON file.
    """
    mock_file_content = (
        '[{"name": "Scenario 1", "parameters_to_vary": ["param1"], '
        '"variations": [{"type": "percentage", "value": 0.1}]}]'
    )
    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        scenarios = load_dsa_scenarios("dummy_path.json")
        assert len(scenarios) == 1
        assert scenarios[0]["name"] == "Scenario 1"


def test_load_dsa_scenarios_file_not_found() -> None:
    """Tests that FileNotFoundError is raised for a missing file."""
    with pytest.raises(FileNotFoundError):
        load_dsa_scenarios("non_existent_file.json")


def test_load_dsa_scenarios_invalid_json() -> None:
    """Tests that ValueError is raised for a malformed JSON file."""
    with patch("builtins.open", mock_open(read_data="{invalid json")):
        with pytest.raises(ValueError, match="Invalid JSON format"):
            load_dsa_scenarios("dummy/path.json")


@pytest.fixture  # type: ignore[misc]
def base_dsa_data() -> Dict[str, Any]:
    """Provides a base set of data for DSA tests."""
    return {
        "base_case_df": pd.DataFrame(
            {
                "category": ["A", "B", "A", "B"],
                "param1": [100, 200, 100, 200],
                "param2": [10, 20, 10, 20],
            }
        ),
        "formulas_data": {
            "outputs": [{"parameter_mapping": {"param1": "param1", "param2": "param2"}}]
        },
        "calculation_pipeline": lambda df, formulas: df.copy(),
    }


def test_run_dsa_analysis_one_way_and_two_way(base_dsa_data: Dict[str, Any]) -> None:
    """
    Tests that one-way and two-way scenarios are applied correctly.
    """
    scenarios = [
        {
            "name": "One-Way",
            "parameters_to_vary": ["param1"],
            "variations": [{"type": "percentage", "value": 0.1}],
        },
        {
            "name": "Two-Way",
            "parameters_to_vary": ["param1", "param2"],
            "variations": [
                {"type": "percentage", "value": -0.2},
                {"type": "absolute", "value": 5},
            ],
        },
    ]
    results = run_dsa_analysis(**base_dsa_data, scenarios=scenarios)
    assert results["One-Way"]["param1"].iloc[0] == pytest.approx(110)
    assert results["Two-Way"]["param1"].iloc[0] == pytest.approx(80)
    assert results["Two-Way"]["param2"].iloc[0] == pytest.approx(15)


def test_run_dsa_analysis_with_row_filter(base_dsa_data: Dict[str, Any]) -> None:
    """
    Tests that scenarios are correctly applied only to rows matching the filter.
    """
    scenarios = [
        {
            "name": "Filter Scenario",
            "parameters_to_vary": ["param1"],
            "variations": [{"type": "absolute", "value": 50}],
            "row_filter": {"category": "A"},
        }
    ]
    results = run_dsa_analysis(**base_dsa_data, scenarios=scenarios)
    result_df = results["Filter Scenario"]

    # Rows where category is 'A' should be changed (100 -> 150)
    assert result_df[result_df["category"] == "A"]["param1"].iloc[0] == 150
    # Rows where category is 'B' should be unchanged (200)
    assert result_df[result_df["category"] == "B"]["param1"].iloc[0] == 200


def test_run_dsa_analysis_int_to_float_conversion(
    base_dsa_data: Dict[str, Any],
) -> None:
    """
    Tests that integer columns are correctly converted to float before variation.
    """
    # Ensure param1 is integer type
    base_dsa_data["base_case_df"]["param1"] = base_dsa_data["base_case_df"][
        "param1"
    ].astype(int)

    scenarios = [
        {
            "name": "Int Scenario",
            "parameters_to_vary": ["param1"],
            "variations": [{"type": "percentage", "value": 0.15}],
        }
    ]
    results = run_dsa_analysis(**base_dsa_data, scenarios=scenarios)
    result_df = results["Int Scenario"]
    assert pd.api.types.is_float_dtype(result_df["param1"])
    assert result_df["param1"].iloc[0] == pytest.approx(115.0)


def test_run_dsa_analysis_unknown_param_warning(
    base_dsa_data: Dict[str, Any], caplog: LogCaptureFixture
) -> None:
    """
    Tests that a warning is logged for a parameter not in the mapping.
    """
    scenarios = [
        {
            "name": "Unknown Param",
            "parameters_to_vary": ["unknown_param"],
            "variations": [{"type": "absolute", "value": 1}],
        }
    ]
    with caplog.at_level(logging.WARNING):
        run_dsa_analysis(**base_dsa_data, scenarios=scenarios)
    assert "Param 'unknown_param' not in formula mapping" in caplog.text


def test_run_dsa_analysis_unknown_variation_warning(
    base_dsa_data: Dict[str, Any], caplog: LogCaptureFixture
) -> None:
    """
    Tests that a warning is logged for an unknown variation type.
    """
    scenarios = [
        {
            "name": "Unknown Variation",
            "parameters_to_vary": ["param1"],
            "variations": [{"type": "exponential", "value": 2}],
        }
    ]
    with caplog.at_level(logging.WARNING):
        run_dsa_analysis(**base_dsa_data, scenarios=scenarios)
    assert "Unknown variation type 'exponential'" in caplog.text


def test_report_dsa_results(caplog: LogCaptureFixture) -> None:
    """
    Tests that the report_dsa_results function logs a summary report correctly.
    """
    base_case_results = pd.DataFrame({"Calculated_Cost_Mid_Y0": [100, 150]})
    dsa_results = {
        "Scenario A": pd.DataFrame({"Calculated_Cost_Mid_Y0": [110, 160]}),
        "Scenario B": pd.DataFrame({"Calculated_Cost_Mid_Y0": [80, 120]}),
    }

    with caplog.at_level(logging.INFO):
        report_dsa_results(dsa_results, base_case_results)

    assert "Base Case Average Cost: 125.00" in caplog.text
    assert "Scenario A" in caplog.text
    assert "Result: 135.00" in caplog.text
    assert "Change: +8.00%" in caplog.text
    assert "Scenario B" in caplog.text
    assert "Result: 100.00" in caplog.text
    assert "Change: -20.00%" in caplog.text
