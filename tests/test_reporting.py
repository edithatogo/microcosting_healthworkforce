# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
# tests/test_reporting.py
"""Test for the reporting module."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import polars as pl
import pytest

from src.reporting import (
    plot_dsa_tornado,
    plot_psa_histogram,
    save_base_case_results,
    save_dsa_results,
    save_psa_results,
)
from tests.checks import assert_that

EXPECTED_3 = 3


@pytest.fixture
def mock_reporting_data() -> dict[str, Any]:
    """Provide a consistent set of mock data for reporting tests."""
    base_case = pl.DataFrame({"A": [1, 2], "B": [3, 4]})
    dsa_results = {
        "Scenario 1": pl.DataFrame({"X": [10, 20], "Y": [30, 40]}),
        "Scenario 2": pl.DataFrame({"X": [15, 25], "Y": [35, 45]}),
    }
    # Add the required column for DSA summary calculation
    dsa_results["Scenario 1"] = dsa_results["Scenario 1"].with_columns(
        pl.Series("Calculated_Cost_Mid_Y0", [100, 110]),
    )
    dsa_results["Scenario 2"] = dsa_results["Scenario 2"].with_columns(
        pl.Series("Calculated_Cost_Mid_Y0", [80, 90]),
    )
    base_case = base_case.with_columns(pl.Series("Calculated_Cost_Mid_Y0", [90, 100]))

    psa_results = pl.DataFrame({"mean_cost": [101, 102, 103]})
    return {
        "base_case": base_case,
        "dsa": dsa_results,
        "psa": psa_results,
    }


@patch("polars.DataFrame.write_csv")
def test_save_base_case_results(
    mock_to_csv: MagicMock,
    mock_reporting_data: dict[str, Any],
) -> None:
    """Test that save_base_case_results calls to_csv with the correct path."""
    save_base_case_results(mock_reporting_data["base_case"], "output")
    mock_to_csv.assert_called_once_with(Path("output/base_case_results.csv"))


@patch("polars.DataFrame.write_csv")
@patch("pathlib.Path.mkdir")
@patch("src.reporting.plot_dsa_tornado")
def test_save_dsa_results(
    mock_plot: MagicMock,
    mock_makedirs: MagicMock,
    mock_to_csv: MagicMock,
    mock_reporting_data: dict[str, Any],
) -> None:
    """Test that save_dsa_results saves both detailed and summary files."""
    # Make os.path.join return whatever it's called with for easy testing

    save_dsa_results(
        mock_reporting_data["dsa"],
        mock_reporting_data["base_case"],
        "output",
    )

    # Check that the detailed directory is created
    mock_makedirs.assert_called_once_with(parents=True, exist_ok=True)

    # Check that detailed files are saved
    assert_that(mock_to_csv.call_count == EXPECTED_3)  # 2 detailed + 1 summary
    mock_to_csv.assert_any_call(Path("output/dsa_detailed/Scenario 1.csv"))
    mock_to_csv.assert_any_call(Path("output/dsa_detailed/Scenario 2.csv"))

    # Check that the summary file is saved
    mock_to_csv.assert_any_call(Path("output/dsa_summary.csv"))

    # Check that the plot function is called
    mock_plot.assert_called_once()


@patch("polars.DataFrame.write_csv")
@patch("src.reporting.plot_psa_histogram")
def test_save_psa_results(
    mock_plot: MagicMock,
    mock_to_csv: MagicMock,
    mock_reporting_data: dict[str, Any],
) -> None:
    """Test that save_psa_results saves the file and calls the plot function."""
    save_psa_results(mock_reporting_data["psa"], "output")
    mock_to_csv.assert_called_once_with(Path("output/psa_results.csv"))
    mock_plot.assert_called_once()


@pytest.mark.usefixtures("mock_reporting_data")
@patch("src.reporting.plt.savefig")
def test_plot_dsa_tornado(
    mock_savefig: MagicMock,
) -> None:
    """Test that the DSA tornado plot function runs without error and calls savefig."""
    summary_df = pl.DataFrame(
        {
            "scenario_name": ["Scenario 1", "Scenario 2"],
            "percentage_change": [10, -5],
        },
    )
    plot_dsa_tornado(summary_df, "output")
    mock_savefig.assert_called_once()


@patch("src.reporting.plt.savefig")
def test_plot_psa_histogram(
    mock_savefig: MagicMock,
    mock_reporting_data: dict[str, Any],
) -> None:
    """Verify the PSA histogram calls the figure exporter."""
    plot_psa_histogram(mock_reporting_data["psa"], "output")
    mock_savefig.assert_called_once()


def join_path(*args: str) -> str:
    """Join fixture path components without filesystem access."""
    return "/".join(args)
