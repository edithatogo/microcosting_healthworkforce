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


def test_validate_psa_results(caplog: Any) -> None:
    """
    Tests that the validate_psa_results function logs a warning.
    """
    psa_results = pd.DataFrame({"mean_cost": [100, 110, 120]})
    validation_df = pd.DataFrame()
    with caplog.at_level(logging.WARNING):
        validate_psa_results(psa_results, validation_df)
    assert "PSA validation is not yet fully implemented." in caplog.text
