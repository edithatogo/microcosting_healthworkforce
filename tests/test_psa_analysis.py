# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
# tests/test_psa_analysis.py
"""Test for the psa_analysis module."""

import logging
from typing import Any
from unittest.mock import mock_open, patch

import polars as pl
import pytest
from pydantic import ValidationError
lazy from _pytest.logging import LogCaptureFixture

from src.formula_engine import apply_formulas
from src.psa_analysis import (
    load_psa_scenarios,
    report_psa_results,
    run_psa_analysis,
)
from tests.checks import assert_that

EXPECTED_5 = 5
EXPECTED_200 = 200


def test_load_psa_scenarios_success() -> None:
    """Load an intact PSA scenario list from valid JSON."""
    mock_file_content = (
        '[{"parameter_to_vary": "param1", "distribution": {"type": "normal", '
        '"mean": 0, "std_dev": 1}}]'
    )
    with patch("pathlib.Path.open", mock_open(read_data=mock_file_content)):
        scenarios = load_psa_scenarios("dummy_path.json")
        assert_that(len(scenarios) == 1)
        assert_that(scenarios[0]["parameter_to_vary"] == "param1")


def test_load_psa_scenarios_file_not_found() -> None:
    """Test that FileNotFoundError is raised for a missing file."""
    with pytest.raises(FileNotFoundError):
        load_psa_scenarios("non_existent_file.json")


def test_load_psa_scenarios_invalid_json() -> None:
    """Test that ValueError is raised for a malformed JSON file."""
    with (
        patch("pathlib.Path.open", mock_open(read_data="{invalid json")),
        pytest.raises(ValueError, match="Invalid JSON format"),
    ):
        load_psa_scenarios("dummy/path.json")


def mock_calculation_pipeline(
    df: pl.DataFrame,
    _formulas: dict[str, Any],
) -> pl.DataFrame:
    """Return the synthetic calculation used to isolate scenario mechanics."""
    return df.with_columns((pl.col("param1") * 2).alias("Calculated_Cost_Mid_Y0"))


@pytest.fixture
def base_test_data() -> dict[str, Any]:
    """Provide a base set of data for PSA tests."""
    return {
        "base_case_df": pl.DataFrame({"param1": [100], "param2": [200]}),
        "formulas_data": {"outputs": [{"parameter_mapping": {"param1": "param1"}}]},
        "calculation_pipeline": mock_calculation_pipeline,
    }


@pytest.mark.parametrize(
    ("dist_type", "dist_params"),
    [
        ("normal", {"type": "normal", "mean": 110, "std_dev": 10}),
        ("uniform", {"type": "uniform", "min": 90, "max": 110}),
        ("triangular", {"type": "triangular", "min": 90, "mode": 100, "max": 110}),
    ],
)
def test_run_psa_analysis_distributions(
    base_test_data: dict[str, Any],
    dist_type: str,
    dist_params: dict[str, Any],
) -> None:
    """Test that PSA runs correctly for all supported distribution types."""
    assert_that(dist_params["type"] == dist_type)
    scenarios = [{"parameter_to_vary": "param1", "distribution": dist_params}]
    psa_results = run_psa_analysis(**base_test_data, scenarios=scenarios, iterations=5)
    assert_that(len(psa_results) == EXPECTED_5)
    assert_that("mean_cost" in psa_results.columns)
    # Check that the cost is not the base case cost of 200
    assert_that(psa_results["mean_cost"][0] != EXPECTED_200)


def test_run_psa_analysis_unknown_param_rejected(
    base_test_data: dict[str, Any],
) -> None:
    """Reject an unmapped parameter instead of silently omitting uncertainty."""
    scenarios = [
        {
            "parameter_to_vary": "unknown_param",
            "distribution": {"type": "normal", "mean": 1, "std_dev": 0.1},
        },
    ]
    with pytest.raises(ValueError, match="unmapped parameter"):
        run_psa_analysis(**base_test_data, scenarios=scenarios, iterations=1)


def test_run_psa_analysis_unknown_dist_rejected(
    base_test_data: dict[str, Any],
) -> None:
    """Reject an unsupported distribution instead of running a partial model."""
    scenarios = [
        {
            "parameter_to_vary": "param1",
            "distribution": {"type": "unknown_dist"},
        },
    ]
    with pytest.raises(ValidationError):
        run_psa_analysis(**base_test_data, scenarios=scenarios, iterations=1)


def test_report_psa_results_summary(caplog: LogCaptureFixture) -> None:
    """Test that the report_psa_results function logs a summary report correctly."""
    psa_results_df = pl.DataFrame({"mean_cost": [100, 110, 120]})
    with caplog.at_level(logging.INFO):
        report_psa_results(psa_results_df)
    assert_that("PSA Results Summary" in caplog.text)
    assert_that("Exploratory PSA" in caplog.text)
    assert_that("not scientifically validated" in caplog.text)
    assert_that("Average Mean Cost: 110.00" in caplog.text)


def test_report_psa_results_empty(caplog: LogCaptureFixture) -> None:
    """Test that a message is logged when the PSA results DataFrame is empty."""
    with caplog.at_level(logging.INFO):
        report_psa_results(pl.DataFrame())
    assert_that("No PSA results to report" in caplog.text)


def test_report_psa_results_linear_percentiles(caplog: LogCaptureFixture) -> None:
    """Catch a changed quantile definition in the reported simulation interval."""
    with caplog.at_level(logging.INFO):
        report_psa_results(pl.DataFrame({"mean_cost": [100.0, 110.0, 120.0]}))
    assert_that("(100.50 - 119.50)" in caplog.text)
    assert_that("simulation percentile interval" in caplog.text)


def test_psa_recomputes_precalculated_base_costs() -> None:
    """Catch cached base costs suppressing an actual parameter perturbation."""
    document: dict[str, Any] = {
        "formulas": [
            {
                "id": "cost",
                "expression": "salary * (1 + rate)",
                "parameters": ["salary", "rate"],
            },
        ],
        "outputs": [
            {
                "name": "Calculated_Cost_Mid",
                "calculation_method": "formula",
                "uses_formula": "cost",
                "parameter_mapping": {"salary": "salary", "rate": "rate"},
            },
        ],
    }
    original = apply_formulas(
        pl.DataFrame({"salary": [100.0, 200.0], "rate": [0.0, 0.0]}),
        document,
    )
    result = run_psa_analysis(
        original,
        document,
        apply_formulas,
        [
            {
                "parameter_to_vary": "rate",
                "distribution": {"type": "normal", "mean": 1.0, "std_dev": 0.0},
            },
        ],
        iterations=1,
    )
    assert_that(result["mean_cost"].to_list() == [300.0])
    assert_that(original["Calculated_Cost_Mid_Y0"].to_list() == [100.0, 200.0])


def test_single_iteration_report_does_not_invent_precision(
    caplog: LogCaptureFixture,
) -> None:
    """Report a single draw without claiming estimable deviation or an interval."""
    with caplog.at_level(logging.INFO):
        report_psa_results(pl.DataFrame({"mean_cost": [110.0]}))
    assert_that("Average Mean Cost: 110.00" in caplog.text)
    assert_that("undefined" in caplog.text)
    assert_that("not estimated" in caplog.text)
