# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
# tests/test_validation.py
"""Test for the validation module."""

import polars as pl

from src.validation import validate_dsa_results, validate_psa_results
from tests.checks import assert_that


def test_validate_dsa_results_success() -> None:
    """Accept DSA results that agree with their reference."""
    dsa_results = {"Scenario A": pl.DataFrame({"Calculated_Cost_Mid_Y0": [100]})}
    validation_df = pl.DataFrame({"Scenario A_Base Salary + Costs_MP": [100]})
    scenario_map = {"Scenario A": "Scenario A_Base Salary + Costs_MP"}
    assert_that(validate_dsa_results(dsa_results, validation_df, scenario_map))


def test_validate_dsa_results_failure() -> None:
    """Reject DSA results that disagree with their reference."""
    dsa_results = {"Scenario A": pl.DataFrame({"Calculated_Cost_Mid_Y0": [110]})}
    validation_df = pl.DataFrame({"Scenario A_Base Salary + Costs_MP": [100]})
    scenario_map = {"Scenario A": "Scenario A_Base Salary + Costs_MP"}
    assert_that(not validate_dsa_results(dsa_results, validation_df, scenario_map))


def test_validate_psa_results_success() -> None:
    """Accept PSA results that agree with their reference."""
    psa_results = pl.DataFrame({"mean_cost": [100, 110, 120]})
    validation_df = pl.DataFrame({"Expected Mean Cost": [110]})
    assert_that(validate_psa_results(psa_results, validation_df))


def test_validate_psa_results_failure() -> None:
    """Reject PSA results that disagree with their reference."""
    psa_results = pl.DataFrame({"mean_cost": [100, 110, 120]})
    validation_df = pl.DataFrame({"Expected Mean Cost": [150]})
    assert_that(not validate_psa_results(psa_results, validation_df))


def test_validate_psa_results_empty_results() -> None:
    """Test that the validate_psa_results function returns True for empty results."""
    psa_results = pl.DataFrame({"mean_cost": []})
    validation_df = pl.DataFrame({"Expected Mean Cost": [150]})
    assert_that(validate_psa_results(psa_results, validation_df))


def test_validate_psa_results_missing_validation_column() -> None:
    """Report a missing reference column without claiming validation."""
    psa_results = pl.DataFrame({"mean_cost": [100, 110, 120]})
    validation_df = pl.DataFrame({"Some Other Column": [150]})
    assert_that(not validate_psa_results(psa_results, validation_df))
