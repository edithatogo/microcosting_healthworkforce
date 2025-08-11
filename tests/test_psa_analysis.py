# tests/test_psa_analysis.py
"""
Tests for the psa_analysis module.
"""

import logging
from typing import Any, Dict
from unittest.mock import mock_open, patch

import pandas as pd
import pytest
from _pytest.logging import LogCaptureFixture

from src.psa_analysis import (
    load_psa_scenarios,
    report_psa_results,
    run_psa_analysis,
)


def test_load_psa_scenarios_success() -> None:
    """
    Tests that the load_psa_scenarios function loads scenarios correctly from a
    JSON file.
    """
    mock_file_content = (
        '[{"parameter_to_vary": "param1", "distribution": {"type": "normal", '
        '"mean": 0, "std_dev": 1}}]'
    )
    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        scenarios = load_psa_scenarios("dummy_path.json")
        assert len(scenarios) == 1
        assert scenarios[0]["parameter_to_vary"] == "param1"


def test_load_psa_scenarios_file_not_found() -> None:
    """Tests that FileNotFoundError is raised for a missing file."""
    with pytest.raises(FileNotFoundError):
        load_psa_scenarios("non_existent_file.json")


def test_load_psa_scenarios_invalid_json() -> None:
    """Tests that ValueError is raised for a malformed JSON file."""
    with patch("builtins.open", mock_open(read_data="{invalid json")):
        with pytest.raises(ValueError, match="Invalid JSON format"):
            load_psa_scenarios("dummy/path.json")


def mock_calculation_pipeline(
    df: pd.DataFrame, formulas: Dict[str, Any]
) -> pd.DataFrame:
    """A simple mock calculation pipeline for testing."""
    df["Calculated_Cost_Mid_Y0"] = df["param1"] * 2
    return df


@pytest.fixture  # type: ignore[misc]
def base_test_data() -> Dict[str, Any]:
    """Provides a base set of data for PSA tests."""
    return {
        "base_case_df": pd.DataFrame({"param1": [100], "param2": [200]}),
        "formulas_data": {"outputs": [{"parameter_mapping": {"param1": "param1"}}]},
        "calculation_pipeline": mock_calculation_pipeline,
    }


@pytest.mark.parametrize(  # type: ignore[misc]
    "dist_type, dist_params",
    [
        ("normal", {"type": "normal", "mean": 110, "std_dev": 10}),
        ("uniform", {"type": "uniform", "min": 90, "max": 110}),
        ("triangular", {"type": "triangular", "min": 90, "mode": 100, "max": 110}),
    ],
)
def test_run_psa_analysis_distributions(
    base_test_data: Dict[str, Any], dist_type: str, dist_params: Dict[str, Any]
) -> None:
    """
    Tests that PSA runs correctly for all supported distribution types.
    """
    scenarios = [{"parameter_to_vary": "param1", "distribution": dist_params}]
    psa_results = run_psa_analysis(**base_test_data, scenarios=scenarios, iterations=5)
    assert len(psa_results) == 5
    assert "mean_cost" in psa_results.columns
    # Check that the cost is not the base case cost of 200
    assert psa_results["mean_cost"].iloc[0] != 200


def test_run_psa_analysis_unknown_param_warning(
    base_test_data: Dict[str, Any], caplog: LogCaptureFixture
) -> None:
    """
    Tests that a warning is logged for a parameter not in the mapping.
    """
    scenarios = [
        {
            "parameter_to_vary": "unknown_param",
            "distribution": {"type": "normal", "mean": 1, "std_dev": 0.1},
        }
    ]
    with caplog.at_level(logging.WARNING):
        run_psa_analysis(**base_test_data, scenarios=scenarios, iterations=1)
    assert "Param 'unknown_param' not in formula mapping" in caplog.text


def test_run_psa_analysis_unknown_dist_warning(
    base_test_data: Dict[str, Any], caplog: LogCaptureFixture
) -> None:
    """
    Tests that a warning is logged for an unknown distribution type.
    """
    scenarios = [
        {
            "parameter_to_vary": "param1",
            "distribution": {"type": "unknown_dist"},
        }
    ]
    with caplog.at_level(logging.WARNING):
        run_psa_analysis(**base_test_data, scenarios=scenarios, iterations=1)
    assert "Unknown distribution 'unknown_dist'" in caplog.text


def test_report_psa_results_summary(caplog: LogCaptureFixture) -> None:
    """
    Tests that the report_psa_results function logs a summary report correctly.
    """
    psa_results_df = pd.DataFrame({"mean_cost": [100, 110, 120]})
    with caplog.at_level(logging.INFO):
        report_psa_results(psa_results_df)
    assert "PSA Results Summary" in caplog.text
    assert "Average Mean Cost: 110.00" in caplog.text


def test_report_psa_results_empty(caplog: LogCaptureFixture) -> None:
    """
    Tests that a message is logged when the PSA results DataFrame is empty.
    """

    with caplog.at_level(logging.INFO):
        report_psa_results(pd.DataFrame())
    assert "No PSA results to report" in caplog.text
