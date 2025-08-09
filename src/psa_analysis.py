# src/psa_analysis.py
"""
This module handles the Probabilistic Sensitivity Analysis (PSA).

It provides functionality to run Monte Carlo simulations, systematically
varying input parameters based on probability distributions to assess their
combined impact on the final calculated costs.
"""

import json
import logging
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
    """
    logging.info(f"--- Running {iterations} PSA Iterations ---")
    all_results = []

    param_to_col_map: Dict[str, str] = {}
    for output_def in formulas_data.get("outputs", []):
        if "parameter_mapping" in output_def:
            param_to_col_map.update(output_def["parameter_mapping"])

    for i in range(iterations):
        if (i + 1) % 100 == 0:
            logging.info(f"Running iteration {i + 1}/{iterations}...")

        iter_df = base_case_df.copy(deep=True)

        for scenario in scenarios:
            param = scenario["parameter_to_vary"]
            dist = scenario["distribution"]
            column_to_vary = param_to_col_map.get(param)

            if not column_to_vary:
                logging.warning(f"Param '{param}' not in formula mapping. Skipping.")
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
                logging.warning(f"Unknown distribution '{dist['type']}'. Skipping.")
                continue

            iter_df[column_to_vary] = sampled_value

        result_df = calculation_pipeline(iter_df, formulas_data)
        mean_cost = result_df["Calculated_Cost_Mid_Y0"].mean()
        all_results.append({"iteration": i + 1, "mean_cost": mean_cost})

    return pd.DataFrame(all_results)


def report_psa_results(psa_results_df: pd.DataFrame) -> None:
    """
    Prints a summary report of the PSA results.
    """
    logging.info("--- PSA Results Summary ---")
    if psa_results_df.empty:
        logging.info("No PSA results to report.")
        return

    mean_cost = psa_results_df["mean_cost"].mean()
    std_dev = psa_results_df["mean_cost"].std()
    confidence_interval = (
        psa_results_df["mean_cost"].quantile(0.025),
        psa_results_df["mean_cost"].quantile(0.975),
    )

    logging.info(f"Number of Iterations: {len(psa_results_df)}")
    logging.info(f"Average Mean Cost: {mean_cost:,.2f}")
    logging.info(f"Standard Deviation: {std_dev:,.2f}")
    logging.info(
        f"95% Confidence Interval: ({confidence_interval[0]:,.2f} - "
        f"{confidence_interval[1]:,.2f})"
    )
