# src/sensitivity_analysis.py
"""
This module handles the Deterministic Sensitivity Analysis (DSA).

It provides functionality to run pre-defined or custom scenarios,
systematically varying input parameters to assess their impact on the final
calculated costs.
"""

import json
from typing import Any, Callable, Dict, List, cast

import pandas as pd


def load_dsa_scenarios(file_path: str) -> List[Dict[str, Any]]:
    """
    Loads the DSA scenario definitions from a specified JSON file.
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
    formulas_data: Dict[str, Any],
    calculation_pipeline: Callable[[pd.DataFrame, Dict[str, Any]], pd.DataFrame],
    scenarios: List[Dict[str, Any]] | None = None,
    custom_scenarios: List[Dict[str, Any]] | None = None,
) -> Dict[str, pd.DataFrame]:
    """
    Runs a series of Deterministic Sensitivity Analysis scenarios.

    It can use a pre-defined list of scenarios or a custom list provided at
    runtime. The custom scenarios also support row-level filtering.

    Args:
        base_case_df: The DataFrame with the base case input data.
        formulas_data: The dictionary of formula definitions.
        calculation_pipeline: The function that runs the full calculation.
        scenarios: A list of pre-defined scenarios to run.
        custom_scenarios: A list of custom scenarios to run instead of the
                          pre-defined ones.

    Returns:
        A dictionary where keys are scenario names and values are the resulting
        DataFrames.
    """
    results: Dict[str, pd.DataFrame] = {}
    scenarios_to_run = custom_scenarios if custom_scenarios is not None else scenarios

    if not scenarios_to_run:
        print("No DSA scenarios provided. Skipping.")
        return {}

    print(f"\n--- Running {len(scenarios_to_run)} DSA Scenarios ---")

    # Get the mapping from the formula definition to find the correct column
    # This assumes the first output definition is representative.
    param_to_col_map = formulas_data["outputs"][0]["parameter_mapping"]

    for scenario in scenarios_to_run:
        scenario_name = scenario["name"]
        param_to_vary = scenario["parameter_to_vary"]
        variation = scenario["variation"]
        row_filter = scenario.get("row_filter")  # Get the optional row filter
        print(f"  - Running scenario: {scenario_name}")

        # Create a deep copy to avoid modifying the base DataFrame
        scenario_df = base_case_df.copy(deep=True)

        # Find the source column in the DataFrame for the parameter
        if param_to_vary not in param_to_col_map:
            print(f"Warning: Param '{param_to_vary}' not in formula mapping. Skipping.")
            continue

        column_to_vary = param_to_col_map[param_to_vary]

        # Determine which rows to apply the variation to
        if row_filter:
            mask = pd.Series(True, index=scenario_df.index)
            for key, value in row_filter.items():
                mask &= scenario_df[key] == value
        else:
            # If no filter, apply to all rows
            mask = pd.Series(True, index=scenario_df.index)

        # Apply the variation
        if variation["type"] == "percentage":
            scenario_df.loc[mask, column_to_vary] *= 1 + variation["value"]
        elif variation["type"] == "absolute":
            scenario_df.loc[mask, column_to_vary] += variation["value"]
        else:
            print(f"Warning: Unknown variation type '{variation['type']}'. Skipping.")
            continue

        # Run the full calculation pipeline with the modified data
        scenario_results = calculation_pipeline(scenario_df, formulas_data)
        results[scenario_name] = scenario_results

    print("-------------------------------------\n")
    return results
