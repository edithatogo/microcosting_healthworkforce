# tests/test_psa_analysis.py
"""
Tests for the psa_analysis module.
"""

import logging
from typing import Any, Dict, List
from unittest.mock import mock_open, patch

import pandas as pd
import pytest

from src.psa_analysis import (
    load_psa_scenarios,
    report_psa_results,
    run_psa_analysis,
)


def test_load_psa_scenarios() -> None:
    """
    Tests that the load_psa_scenarios function loads scenarios correctly from a
    JSON file.
    """
    mock_file_content = (
        '[{"parameter_to_vary": "param1", "distribution": {"type": "normal", '
        '"mean": 0, "std_dev": 1}}]'
    )
    with patch("builtins.open", mock_open(read_data=mock_file_content)) as mock_file:
        scenarios = load_psa_scenarios("dummy_path.json")
        mock_file.assert_called_once_with("dummy_path.json", "r")
        assert len(scenarios) == 1
        assert scenarios[0]["parameter_to_vary"] == "param1"


def test_run_psa_analysis() -> None:
    """
    Tests that the run_psa_analysis function correctly applies scenarios and
    returns results.
    """
    base_case_df = pd.DataFrame({"param1": [100], "param2": [200]})
    formulas_data = {"outputs": [{"parameter_mapping": {"param1": "param1"}}]}
    scenarios: List[Dict[str, Any]] = [
        {
            "parameter_to_vary": "param1",
            "distribution": {"type": "normal", "mean": 110, "std_dev": 10},
        }
    ]

    def mock_calculation_pipeline(
        df: pd.DataFrame, formulas: Dict[str, Any]
    ) -> pd.DataFrame:
        df["Calculated_Cost_Mid_Y0"] = 100
        return df

    psa_results = run_psa_analysis(
        base_case_df, formulas_data, mock_calculation_pipeline, scenarios, 10
    )

    assert len(psa_results) == 10
    assert "iteration" in psa_results.columns
    assert "mean_cost" in psa_results.columns


def test_report_psa_results(caplog: Any) -> None:
    """
    Tests that the report_psa_results function logs a summary report correctly.
    """
    psa_results_df = pd.DataFrame({"mean_cost": [100, 110, 120]})

    with caplog.at_level(logging.INFO):
        report_psa_results(psa_results_df)

    assert "PSA Results Summary" in caplog.text
    assert "Average Mean Cost" in caplog.text
    assert "Standard Deviation" in caplog.text
    assert "95% Confidence Interval" in caplog.text
