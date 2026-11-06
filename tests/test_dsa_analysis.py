# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
# tests/test_dsa_analysis.py
"""Test for the dsa_analysis module."""

import logging
from typing import Any
from unittest.mock import mock_open, patch

import polars as pl
import pytest
lazy from _pytest.logging import LogCaptureFixture

from src.dsa_analysis import (
    load_dsa_scenarios,
    report_dsa_results,
    run_dsa_analysis,
)
from src.formula_engine import apply_formulas
from tests.checks import assert_that

EXPECTED_150 = 150
EXPECTED_200 = 200


def test_dsa_recalculates_an_already_costed_base_case() -> None:
    """Perturbing raw inputs must not retain an old calculated cost."""
    formulas: dict[str, Any] = {
        "formulas": [
            {"id": "salary_cost", "expression": "salary", "parameters": ["salary"]},
        ],
        "outputs": [
            {
                "name": "Calculated_Cost_Mid",
                "calculation_method": "formula",
                "uses_formula": "salary_cost",
                "parameter_mapping": {"salary": "salary"},
            },
        ],
    }
    raw = pl.DataFrame({"salary": [100.0]})
    costed = apply_formulas(raw, formulas)
    scenarios = [
        {
            "name": "increase",
            "parameter_to_vary": "salary",
            "variation": {"type": "percentage", "value": 0.5},
        },
    ]
    from_raw = run_dsa_analysis(raw, formulas, apply_formulas, scenarios)["increase"]
    from_costed = run_dsa_analysis(costed, formulas, apply_formulas, scenarios)[
        "increase"
    ]
    assert_that(from_costed["salary"][0] == EXPECTED_150)
    assert_that(from_costed["Calculated_Cost_Mid_Y0"][0] == EXPECTED_150)
    assert_that(from_costed.equals(from_raw))


def test_load_dsa_scenarios_success() -> None:
    """Load an intact DSA scenario list from valid JSON."""
    mock_file_content = (
        '[{"name": "Scenario 1", "parameters_to_vary": ["param1"], '
        '"variations": [{"type": "percentage", "value": 0.1}]}]'
    )
    with patch("pathlib.Path.open", mock_open(read_data=mock_file_content)):
        scenarios = load_dsa_scenarios("dummy_path.json")
        assert_that(len(scenarios) == 1)
        assert_that(scenarios[0]["name"] == "Scenario 1")


def test_load_dsa_scenarios_file_not_found() -> None:
    """Test that FileNotFoundError is raised for a missing file."""
    with pytest.raises(FileNotFoundError):
        load_dsa_scenarios("non_existent_file.json")


def test_load_dsa_scenarios_invalid_json() -> None:
    """Test that ValueError is raised for a malformed JSON file."""
    with (
        patch("pathlib.Path.open", mock_open(read_data="{invalid json")),
        pytest.raises(ValueError, match="Invalid JSON format"),
    ):
        load_dsa_scenarios("dummy/path.json")


@pytest.fixture
def base_dsa_data() -> dict[str, Any]:
    """Provide a base set of data for DSA tests."""
    return {
        "base_case_df": pl.DataFrame(
            {
                "category": ["A", "B", "A", "B"],
                "param1": [100, 200, 100, 200],
                "param2": [10, 20, 10, 20],
            },
        ),
        "formulas_data": {
            "outputs": [
                {"parameter_mapping": {"param1": "param1", "param2": "param2"}},
            ],
        },
        "calculation_pipeline": clone_pipeline,
    }


def test_run_dsa_analysis_one_way_and_two_way(base_dsa_data: dict[str, Any]) -> None:
    """Test that one-way and two-way scenarios are applied correctly."""
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
    assert_that(results["One-Way"]["param1"][0] == pytest.approx(110))
    assert_that(results["Two-Way"]["param1"][0] == pytest.approx(80))
    assert_that(results["Two-Way"]["param2"][0] == pytest.approx(15))


def test_run_dsa_analysis_with_row_filter(base_dsa_data: dict[str, Any]) -> None:
    """Test that scenarios are correctly applied only to rows matching the filter."""
    scenarios = [
        {
            "name": "Filter Scenario",
            "parameters_to_vary": ["param1"],
            "variations": [{"type": "absolute", "value": 50}],
            "row_filter": {"category": "A"},
        },
    ]
    results = run_dsa_analysis(**base_dsa_data, scenarios=scenarios)
    result_df = results["Filter Scenario"]

    # Rows where category is 'A' should be changed (100 -> 150)
    assert_that(
        result_df.filter(pl.col("category") == "A")["param1"][0] == EXPECTED_150,
    )
    # Rows where category is 'B' should be unchanged (200)
    assert_that(
        result_df.filter(pl.col("category") == "B")["param1"][0] == EXPECTED_200,
    )


def test_run_dsa_analysis_int_to_float_conversion(
    base_dsa_data: dict[str, Any],
) -> None:
    """Test that integer columns are correctly converted to float before variation."""
    # Ensure param1 is integer type
    assert_that(base_dsa_data["base_case_df"]["param1"].dtype.is_integer())

    scenarios = [
        {
            "name": "Int Scenario",
            "parameters_to_vary": ["param1"],
            "variations": [{"type": "percentage", "value": 0.15}],
        },
    ]
    results = run_dsa_analysis(**base_dsa_data, scenarios=scenarios)
    result_df = results["Int Scenario"]
    assert_that(result_df["param1"].dtype.is_float())
    assert_that(result_df["param1"][0] == pytest.approx(115.0))


def test_run_dsa_analysis_unknown_param_warning(
    base_dsa_data: dict[str, Any],
    caplog: LogCaptureFixture,
) -> None:
    """Test that a warning is logged for a parameter not in the mapping."""
    scenarios = [
        {
            "name": "Unknown Param",
            "parameters_to_vary": ["unknown_param"],
            "variations": [{"type": "absolute", "value": 1}],
        },
    ]
    with caplog.at_level(logging.WARNING):
        run_dsa_analysis(**base_dsa_data, scenarios=scenarios)
    assert_that("Param 'unknown_param' not in formula mapping" in caplog.text)


def test_run_dsa_analysis_unknown_variation_warning(
    base_dsa_data: dict[str, Any],
    caplog: LogCaptureFixture,
) -> None:
    """Test that a warning is logged for an unknown variation type."""
    scenarios = [
        {
            "name": "Unknown Variation",
            "parameters_to_vary": ["param1"],
            "variations": [{"type": "exponential", "value": 2}],
        },
    ]
    with caplog.at_level(logging.WARNING):
        run_dsa_analysis(**base_dsa_data, scenarios=scenarios)
    assert_that("Unknown variation type 'exponential'" in caplog.text)


def test_report_dsa_results(caplog: LogCaptureFixture) -> None:
    """Test that the report_dsa_results function logs a summary report correctly."""
    base_case_results = pl.DataFrame({"Calculated_Cost_Mid_Y0": [100, 150]})
    dsa_results = {
        "Scenario A": pl.DataFrame({"Calculated_Cost_Mid_Y0": [110, 160]}),
        "Scenario B": pl.DataFrame({"Calculated_Cost_Mid_Y0": [80, 120]}),
    }

    with caplog.at_level(logging.INFO):
        report_dsa_results(dsa_results, base_case_results)

    assert_that("Base Case Average Cost: 125.00" in caplog.text)
    assert_that("Scenario A" in caplog.text)
    assert_that("Result: 135.00" in caplog.text)
    assert_that("Change: +8.00%" in caplog.text)
    assert_that("Scenario B" in caplog.text)
    assert_that("Result: 100.00" in caplog.text)
    assert_that("Change: -20.00%" in caplog.text)


def clone_pipeline(df: pl.DataFrame, _formulas: dict[str, Any]) -> pl.DataFrame:
    """Preserve input rows in the DSA pipeline fixture."""
    return df.clone()
