# tests/test_reporting.py
"""
Tests for the reporting module.
"""

from typing import Any, Dict
from unittest.mock import patch

import pandas as pd
import pytest

from src.reporting import (
    plot_dsa_tornado,
    plot_psa_histogram,
    save_base_case_results,
    save_dsa_results,
    save_psa_results,
)


@pytest.fixture  # type: ignore[misc]
def mock_reporting_data() -> Dict[str, Any]:
    """Provides a consistent set of mock data for reporting tests."""
    base_case = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    dsa_results = {
        "Scenario 1": pd.DataFrame({"X": [10, 20], "Y": [30, 40]}),
        "Scenario 2": pd.DataFrame({"X": [15, 25], "Y": [35, 45]}),
    }
    # Add the required column for DSA summary calculation
    dsa_results["Scenario 1"]["Calculated_Cost_Mid_Y0"] = [100, 110]
    dsa_results["Scenario 2"]["Calculated_Cost_Mid_Y0"] = [80, 90]
    base_case["Calculated_Cost_Mid_Y0"] = [90, 100]

    psa_results = pd.DataFrame({"mean_cost": [101, 102, 103]})
    return {
        "base_case": base_case,
        "dsa": dsa_results,
        "psa": psa_results,
    }


@patch("src.reporting.os.path.join", return_value="mock/path/file.csv")
@patch("pandas.DataFrame.to_csv")
def test_save_base_case_results(
    mock_to_csv: Any, mock_path_join: Any, mock_reporting_data: Dict[str, Any]
) -> None:
    """
    Tests that save_base_case_results calls to_csv with the correct path.
    """
    save_base_case_results(mock_reporting_data["base_case"], "output")
    mock_path_join.assert_called_once_with("output", "base_case_results.csv")
    mock_to_csv.assert_called_once_with("mock/path/file.csv", index=False)


@patch("src.reporting.os.path.join")
@patch("pandas.DataFrame.to_csv")
@patch("src.reporting.os.makedirs")
@patch("src.reporting.plot_dsa_tornado")
def test_save_dsa_results(
    mock_plot: Any,
    mock_makedirs: Any,
    mock_to_csv: Any,
    mock_path_join: Any,
    mock_reporting_data: Dict[str, Any],
) -> None:
    """
    Tests that save_dsa_results saves both detailed and summary files.
    """
    # Make os.path.join return whatever it's called with for easy testing
    mock_path_join.side_effect = lambda *args: "/".join(args)

    save_dsa_results(
        mock_reporting_data["dsa"], mock_reporting_data["base_case"], "output"
    )

    # Check that the detailed directory is created
    mock_makedirs.assert_called_once_with("output/dsa_detailed", exist_ok=True)

    # Check that detailed files are saved
    assert mock_to_csv.call_count == 3  # 2 detailed + 1 summary
    mock_to_csv.assert_any_call("output/dsa_detailed/Scenario 1.csv", index=False)
    mock_to_csv.assert_any_call("output/dsa_detailed/Scenario 2.csv", index=False)

    # Check that the summary file is saved
    mock_to_csv.assert_any_call("output/dsa_summary.csv", index=False)

    # Check that the plot function is called
    mock_plot.assert_called_once()


@patch("src.reporting.os.path.join", return_value="mock/path/file.csv")
@patch("pandas.DataFrame.to_csv")
@patch("src.reporting.plot_psa_histogram")
def test_save_psa_results(
    mock_plot: Any,
    mock_to_csv: Any,
    mock_path_join: Any,
    mock_reporting_data: Dict[str, Any],
) -> None:
    """
    Tests that save_psa_results saves the file and calls the plot function.
    """
    save_psa_results(mock_reporting_data["psa"], "output")
    mock_path_join.assert_called_once_with("output", "psa_results.csv")
    mock_to_csv.assert_called_once_with("mock/path/file.csv", index=False)
    mock_plot.assert_called_once()


@patch("src.reporting.plt.savefig")
def test_plot_dsa_tornado(
    mock_savefig: Any, mock_reporting_data: Dict[str, Any]
) -> None:
    """
    Tests that the DSA tornado plot function runs without error and calls savefig.
    """
    summary_df = pd.DataFrame(
        {
            "scenario_name": ["Scenario 1", "Scenario 2"],
            "percentage_change": [10, -5],
        }
    )
    plot_dsa_tornado(summary_df, "output")
    mock_savefig.assert_called_once()


@patch("src.reporting.plt.savefig")
def test_plot_psa_histogram(
    mock_savefig: Any, mock_reporting_data: Dict[str, Any]
) -> None:
    """
    Tests that the PSA histogram plot function runs without error and calls savefig.
    """
    plot_psa_histogram(mock_reporting_data["psa"], "output")
    mock_savefig.assert_called_once()
