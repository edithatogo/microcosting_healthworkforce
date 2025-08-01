# src/sensitivity_analysis.py
"""
This module handles the Deterministic Sensitivity Analysis (DSA).

It provides functionality to run pre-defined or custom scenarios,
systematically varying input parameters to assess their impact on the final
calculated costs.
"""

import json
from typing import Any, Dict, List, cast

import pandas as pd


def load_dsa_scenarios(file_path: str) -> List[Dict[str, Any]]:
    """
    Loads the DSA scenario definitions from a specified JSON file.

    Args:
        file_path: The absolute path to the JSON file containing the scenarios.

    Returns:
        A list of dictionaries, where each dictionary defines a DSA scenario.
    """
    try:
        with open(file_path, "r") as f:
            scenarios = json.load(f)
        return cast(List[Dict[str, Any]], scenarios)
    except FileNotFoundError:
        raise FileNotFoundError(f"DSA scenarios file not found at: {file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in DSA scenarios file: {file_path}")


def run_dsa(
    base_case_df: pd.DataFrame,
    scenarios: List[Dict[str, Any]],
    # Placeholder for the full calculation pipeline function
    calculation_pipeline: Any,
) -> Dict[str, pd.DataFrame]:
    """
    Runs a series of Deterministic Sensitivity Analysis scenarios.

    (This is a placeholder for the full implementation).

    Args:
        base_case_df: The original DataFrame with the base case data.
        scenarios: A list of scenario objects to run.
        calculation_pipeline: A function that takes a DataFrame and runs the
                              full calculation process (formulas, projection, rates).

    Returns:
        A dictionary where keys are scenario names and values are the resulting
        DataFrames with final calculated costs for that scenario.
    """
    results: Dict[str, pd.DataFrame] = {}
    print(f"\n--- Running {len(scenarios)} DSA Scenarios ---")

    # Placeholder: In the next step, this will loop through scenarios,
    # apply variations, and call the calculation_pipeline.
    for scenario in scenarios:
        print(f"  - Running scenario: {scenario['name']}")

    print("-------------------------------------\n")
    return results
