# tests/test_dsa_analysis.py
"""
Tests for the dsa_analysis module.
"""

import logging
from typing import Any, Dict, List
from unittest.mock import mock_open, patch

import pandas as pd
import pytest

from src.dsa_analysis import (
    load_dsa_scenarios,
    report_dsa_results,
    run_dsa_analysis,
)


def test_load_dsa_scenarios() -> None:
    """
    Tests that the load_dsa_scenarios function loads scenarios correctly from a
    JSON file.
    """
    mock_file_content = (
        '[{"name": "Scenario 1", "parameter_to_vary": "param1", '
        '"variation": {"type": "percentage", "value": 0.1}}]'
    )
    with patch("builtins.open", mock_open(read_data=mock_file_content)) as mock_file:
        scenarios = load_dsa_scenarios("dummy_path.json")
        mock_file.assert_called_once_with("dummy_path.json", "r")
        assert len(scenarios) == 1
        assert scenarios[0]["name"] == "Scenario 1"


def test_run_dsa_analysis() -> None:
    """
    Tests that the run_dsa_analysis function correctly applies scenarios and
    returns results.
    """
    base_case_df = pd.DataFrame({"param1": [100], "param2": [200]})
    formulas_data = {
        "outputs": [{"parameter_mapping": {"param1": "param1", "param2": "param2"}}]
    }
    scenarios: List[Dict[str, Any]] = [
        {
            "name": "One-Way Scenario",
            "parameters_to_vary": ["param1"],
            "variations": [{"type": "percentage", "value": 0.1}],
        },
        {
            "name": "Two-Way Scenario",
            "parameters_to_vary": ["param1", "param2"],
            "variations": [
                {"type": "percentage", "value": 0.1},
                {"type": "absolute", "value": -50},
            ],
        },
    ]

    def mock_calculation_pipeline(
        df: pd.DataFrame, formulas: Dict[str, Any]
    ) -> pd.DataFrame:
        return df.copy()

    dsa_results = run_dsa_analysis(
        base_case_df, formulas_data, mock_calculation_pipeline, scenarios
    )

    assert "One-Way Scenario" in dsa_results
    assert dsa_results["One-Way Scenario"]["param1"][0] == pytest.approx(110)
    assert "Two-Way Scenario" in dsa_results
    assert dsa_results["Two-Way Scenario"]["param1"][0] == pytest.approx(110)
    assert dsa_results["Two-Way Scenario"]["param2"][0] == pytest.approx(150)


def test_run_dsa_analysis_three_way() -> None:
    """
    Tests that the run_dsa_analysis function correctly applies three-way scenarios.
    """
    base_case_df = pd.DataFrame({"param1": [100], "param2": [200], "param3": [300]})
    formulas_data = {
        "outputs": [
            {
                "parameter_mapping": {
                    "param1": "param1",
                    "param2": "param2",
                    "param3": "param3",
                }
            }
        ]
    }
    scenarios: List[Dict[str, Any]] = [
        {
            "name": "Three-Way Scenario",
            "parameters_to_vary": ["param1", "param2", "param3"],
            "variations": [
                {"type": "percentage", "value": 0.1},
                {"type": "absolute", "value": -50},
                {"type": "percentage", "value": 0.2},
            ],
        },
    ]

    def mock_calculation_pipeline(
        df: pd.DataFrame, formulas: Dict[str, Any]
    ) -> pd.DataFrame:
        return df.copy()

    dsa_results = run_dsa_analysis(
        base_case_df, formulas_data, mock_calculation_pipeline, scenarios
    )

    assert "Three-Way Scenario" in dsa_results
    assert dsa_results["Three-Way Scenario"]["param1"][0] == pytest.approx(110)
    assert dsa_results["Three-Way Scenario"]["param2"][0] == pytest.approx(150)
    assert dsa_results["Three-Way Scenario"]["param3"][0] == pytest.approx(360)


def test_report_dsa_results(caplog: Any) -> None:
    """
    Tests that the report_dsa_results function logs a summary report correctly.
    """
    base_case_results = pd.DataFrame({"Calculated_Cost_Mid_Y0": [100]})
    dsa_results = {"Scenario A": pd.DataFrame({"Calculated_Cost_Mid_Y0": [110]})}

    with caplog.at_level(logging.INFO):
        report_dsa_results(dsa_results, base_case_results)

    assert "DSA Results Summary" in caplog.text
    assert "Base Case Average Cost" in caplog.text
    assert "Scenario A" in caplog.text
    assert "+10.00%" in caplog.text
