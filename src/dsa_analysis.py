# src/dsa_analysis.py
"""
This module handles the Deterministic Sensitivity Analysis (DSA).

It provides functionality to run pre-defined or custom scenarios,
systematically varying input parameters to assess their impact on the final
calculated costs.
"""

import json
import logging
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
    """
    dsa_results: Dict[str, pd.DataFrame] = {}
    param_to_col_map = formulas_data["outputs"][0]["parameter_mapping"]

    for scenario in scenarios:
        scenario_name = scenario["name"]
        params_to_vary = scenario.get("parameters_to_vary", [])
        variations = scenario.get("variations", [])
        row_filter = scenario.get("row_filter")
        logging.info(f"Running scenario: {scenario_name}")

        scenario_df = base_case_df.copy(deep=True)

        for i, param_to_vary in enumerate(params_to_vary):
            variation = variations[i]

            if param_to_vary not in param_to_col_map:
                logging.warning(
                    f"Param '{param_to_vary}' not in formula mapping. Skipping."
                )
                continue

            column_to_vary = param_to_col_map[param_to_vary]

            mask = pd.Series(True, index=scenario_df.index)
            if row_filter:
                for key, value in row_filter.items():
                    mask &= scenario_df[key] == value

            if pd.api.types.is_integer_dtype(scenario_df[column_to_vary]):
                scenario_df[column_to_vary] = scenario_df[column_to_vary].astype(float)

            if variation["type"] == "percentage":
                scenario_df.loc[mask, column_to_vary] *= 1 + variation["value"]
            elif variation["type"] == "absolute":
                scenario_df.loc[mask, column_to_vary] += variation["value"]
            else:
                logging.warning(
                    f"Unknown variation type '{variation['type']}'. Skipping."
                )
                continue

        scenario_results = calculation_pipeline(scenario_df, formulas_data)
        dsa_results[scenario_name] = scenario_results

    return dsa_results


def report_dsa_results(
    dsa_results: Dict[str, pd.DataFrame],
    base_case_results: pd.DataFrame,
) -> None:
    """
    Prints a summary report of the DSA results.
    """
    logging.info("--- DSA Results Summary (showing Year 0 Mid-point Cost) ---")
    base_case_cost = base_case_results["Calculated_Cost_Mid_Y0"].mean()
    logging.info(f"Base Case Average Cost: {base_case_cost:,.2f}")

    for scenario_name, result_df in dsa_results.items():
        scenario_cost = result_df["Calculated_Cost_Mid_Y0"].mean()
        percentage_change = ((scenario_cost - base_case_cost) / base_case_cost) * 100
        logging.info(
            f"  - {scenario_name:<25} | "
            f"Result: {scenario_cost:,.2f} | "
            f"Change: {percentage_change:+.2f}%"
        )
