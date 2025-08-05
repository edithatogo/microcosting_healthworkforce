# tests/test_validation.py
"""
Tests for the validation module.
"""

import logging
from typing import Any, Dict

import numpy as np
import pandas as pd
import pytest

from src.validation import validate_dsa_results, validate_psa_results


def test_validate_dsa_results_success() -> None:
    """
    Tests that the validate_dsa_results function returns True when the results
    match the validation data.
    """
    dsa_results = {
        "Scenario A": pd.DataFrame({"Calculated_Cost_Mid_Y0": [100]})
    }
    validation_df = pd.DataFrame(
        {"Scenario A_Base Salary + Costs_MP": [100]}
    )
    scenario_map = {"Scenario A": "Scenario A_Base Salary + Costs_MP"}
    assert validate_dsa_results(dsa_results, validation_df, scenario_map)


def test_validate_dsa_results_failure() -> None:
    """
    Tests that the validate_dsa_results function returns False when the results
    do not match the validation data.
    """
    dsa_results = {
        "Scenario A": pd.DataFrame({"Calculated_Cost_Mid_Y0": [110]})
    }
    validation_df = pd.DataFrame(
        {"Scenario A_Base Salary + Costs_MP": [100]}
    )
    scenario_map = {"Scenario A": "Scenario A_Base Salary + Costs_MP"}
    assert not validate_dsa_results(dsa_results, validation_df, scenario_map)


def test_validate_psa_results_success() -> None:
    """
    Tests that the validate_psa_results function returns True when the mean cost
    matches the expected value.
    """
    psa_results = pd.DataFrame({"mean_cost": [100, 110, 120]})
    validation_df = pd.DataFrame({"Expected Mean Cost": [110]})
    assert validate_psa_results(psa_results, validation_df)


def test_validate_psa_results_failure() -> None:
    """
    Tests that the validate_psa_results function returns False when the mean cost
    does not match the expected value.
    """
    psa_results = pd.DataFrame({"mean_cost": [100, 110, 120]})
    validation_df = pd.DataFrame({"Expected Mean Cost": [150]})
    assert not validate_psa_results(psa_results, validation_df)


def test_validate_psa_results_empty_results() -> None:
    """
    Tests that the validate_psa_results function returns True for empty results.
    """
    psa_results = pd.DataFrame({"mean_cost": []})
    validation_df = pd.DataFrame({"Expected Mean Cost": [150]})
    assert validate_psa_results(psa_results, validation_df)


def test_validate_psa_results_missing_validation_column() -> None:
    """
    Tests that the validate_psa_results function returns False when the
    validation data is missing the 'Expected Mean Cost' column.
    """
    psa_results = pd.DataFrame({"mean_cost": [100, 110, 120]})
    validation_df = pd.DataFrame({"Some Other Column": [150]})
    assert not validate_psa_results(psa_results, validation_df)