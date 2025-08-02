# src/dsa_analysis.py
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


def run_dsa_analysis(
    base_case_df: pd.DataFrame,
    formulas_data: Dict[str, Any],
    calculation_pipeline: Callable[[pd.DataFrame, Dict[str, Any]], pd.DataFrame],
    scenarios: List[Dict[str, Any]],
) -> Dict[str, pd.DataFrame]:
    """
    Runs a series of Deterministic Sensitivity Analysis scenarios.

    Args:
        base_case_df: The DataFrame with the base case input data.
        formulas_data: The dictionary of formula definitions.
        calculation_pipeline: The function that runs the full calculation.
        scenarios: A list of scenarios to run.

    Returns:
        A dictionary where keys are scenario names and values are the resulting
        DataFrames from the calculation pipeline.
    """
    dsa_results: Dict[str, pd.DataFrame] = {}
    param_to_col_map = formulas_data["outputs"][0]["parameter_mapping"]

    for scenario in scenarios:
        scenario_name = scenario["name"]
        param_to_vary = scenario["parameter_to_vary"]
        variation = scenario["variation"]
        row_filter = scenario.get("row_filter")
        print(f"  - Running scenario: {scenario_name}")

        scenario_df = base_case_df.copy(deep=True)

        if param_to_vary not in param_to_col_map:
            print(f"Warning: Param '{param_to_vary}' not in formula mapping. Skipping.")
            continue

        column_to_vary = param_to_col_map[param_to_vary]

        # Create a boolean mask for filtering rows
        if row_filter:
            mask = pd.Series(True, index=scenario_df.index)
            for key, value in row_filter.items():
                mask &= scenario_df[key] == value
        else:
            # If no filter, apply to all rows
            mask = pd.Series(True, index=scenario_df.index)

        # Apply the variation to the selected rows
        if variation["type"] == "percentage":
            scenario_df.loc[mask, column_to_vary] *= 1 + variation["value"]
        elif variation["type"] == "absolute":
            scenario_df.loc[mask, column_to_vary] += variation["value"]
        else:
            print(f"Warning: Unknown variation type '{variation['type']}'. Skipping.")
            continue

        # Run the full calculation pipeline with the modified data
        scenario_results = calculation_pipeline(scenario_df, formulas_data)
        dsa_results[scenario_name] = scenario_results

    return dsa_results


def report_dsa_results(
    dsa_results: Dict[str, pd.DataFrame],
    base_case_results: pd.DataFrame,
) -> None:
    """
    Prints a summary report of the DSA results.

    Args:
        dsa_results: A dictionary of the DSA results from the run_dsa_analysis function.
        base_case_results: The DataFrame of the base case results for comparison.
    """
    print("\n--- DSA Results Summary (showing Year 0 Mid-point Cost) ---")
    base_case_cost = base_case_results["Calculated_Cost_Mid_Y0"].mean()
    print(f"Base Case Average Cost: {base_case_cost:,.2f}")

    for scenario_name, result_df in dsa_results.items():
        scenario_cost = result_df["Calculated_Cost_Mid_Y0"].mean()
        percentage_change = ((scenario_cost - base_case_cost) / base_case_cost) * 100
        print(
            f"  - {scenario_name:<25} | "
            f"Result: {scenario_cost:,.2f} | "
            f"Change: {percentage_change:+.2f}%"
        )
    print(
        "-----------------------------------------------------------\
"
    )
