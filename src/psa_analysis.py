# src/psa_analysis.py
"""
This module handles the Probabilistic Sensitivity Analysis (PSA).

It provides functionality to run Monte Carlo simulations, systematically
varying input parameters based on probability distributions to assess their
combined impact on the final calculated costs.
"""

import json
from typing import Any, Callable, Dict, List, cast

import numpy as np
import pandas as pd


def load_psa_scenarios(file_path: str) -> List[Dict[str, Any]]:
    """
    Loads the PSA scenario definitions from a specified JSON file.
    """
    try:
        with open(file_path, "r") as f:
            scenarios = json.load(f)
        return cast(List[Dict[str, Any]], scenarios)
    except FileNotFoundError:
        raise FileNotFoundError(f"PSA scenarios file not found at: {file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in PSA scenarios file: {file_path}")


def run_psa_analysis(
    base_case_df: pd.DataFrame,
    formulas_data: Dict[str, Any],
    calculation_pipeline: Callable[[pd.DataFrame, Dict[str, Any]], pd.DataFrame],
    scenarios: List[Dict[str, Any]],
    iterations: int,
) -> pd.DataFrame:
    """
    Runs a Probabilistic Sensitivity Analysis using Monte Carlo simulation.

    Args:
        base_case_df: The DataFrame with the base case input data.
        formulas_data: The dictionary of formula definitions.
        calculation_pipeline: The function that runs the full calculation.
        scenarios: A list of PSA scenarios defining the distributions.
        iterations: The number of Monte Carlo simulations to run.

    Returns:
        A DataFrame containing the summary results from all iterations.
    """
    print(f"\n--- Running {iterations} PSA Iterations ---")
    all_results = []
    param_to_col_map = formulas_data["outputs"][0]["parameter_mapping"]

    for i in range(iterations):
        if (i + 1) % 100 == 0:
            print(f"  - Running iteration {i + 1}/{iterations}...")

        iter_df = base_case_df.copy(deep=True)

        # For each scenario, sample a value and apply it
        for scenario in scenarios:
            param = scenario["parameter_to_vary"]
            dist = scenario["distribution"]
            column_to_vary = param_to_col_map.get(param)

            if not column_to_vary:
                print(f"Warning: Param '{param}' not in formula mapping. Skipping.")
                continue

            if dist["type"] == "normal":
                sampled_value = np.random.normal(dist["mean"], dist["std_dev"])
            elif dist["type"] == "uniform":
                sampled_value = np.random.uniform(dist["min"], dist["max"])
            elif dist["type"] == "triangular":
                sampled_value = np.random.triangular(
                    dist["min"], dist["mode"], dist["max"]
                )
            else:
                print(f"Warning: Unknown distribution '{dist['type']}'. Skipping.")
                continue

            iter_df[column_to_vary] = sampled_value

        # Run the pipeline and store the key output
        result_df = calculation_pipeline(iter_df, formulas_data)
        mean_cost = result_df["Calculated_Cost_Mid_Y0"].mean()
        all_results.append({"iteration": i + 1, "mean_cost": mean_cost})

    print("-------------------------------------\n")
    return pd.DataFrame(all_results)


def report_psa_results(psa_results_df: pd.DataFrame) -> None:
    """
    Prints a summary report of the PSA results.

    Args:
        psa_results_df: A DataFrame with the results from the PSA run.
    """
    print("\n--- PSA Results Summary ---")
    if psa_results_df.empty:
        print("No PSA results to report.")
        return

    mean_cost = psa_results_df["mean_cost"].mean()
    std_dev = psa_results_df["mean_cost"].std()
    confidence_interval = (
        psa_results_df["mean_cost"].quantile(0.025),
        psa_results_df["mean_cost"].quantile(0.975),
    )

    print(f"Number of Iterations: {len(psa_results_df)}")
    print(f"Average Mean Cost: {mean_cost:,.2f}")
    print(f"Standard Deviation: {std_dev:,.2f}")
    print(
        f"95% Confidence Interval: ({confidence_interval[0]:,.2f} - "
        f"{confidence_interval[1]:,.2f})"
    )
    print("---------------------------\n")
