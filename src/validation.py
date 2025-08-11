# src/validation.py
"""
This module handles the validation of analysis results against baseline data.

It provides functions to compare the calculated results from the Deterministic
and Probabilistic Sensitivity Analyses (DSA and PSA) against pre-calculated,
trusted values from the original Excel model. This ensures that any changes
to the codebase do not introduce regressions and that the model's outputs
remain accurate.
"""

import logging
from typing import Dict

import numpy as np
import pandas as pd


def validate_dsa_results(
    dsa_results: Dict[str, pd.DataFrame],
    validation_df: pd.DataFrame,
    scenario_map: Dict[str, str],
    tolerance: float = 1e-3,
) -> bool:
    """
    Validates the DSA results against pre-calculated values from a validation sheet.

    This function iterates through each DSA scenario result, looks up the
    corresponding validation column in the `validation_df` using the
    `scenario_map`, and compares the calculated values against the expected
    values using `np.allclose` to account for floating-point inaccuracies.

    Args:
        dsa_results: A dictionary where keys are scenario names and values are
                     the corresponding result DataFrames.
        validation_df: The DataFrame loaded from the DSA validation sheet,
                       containing the expected outcomes.
        scenario_map: A dictionary mapping DSA scenario names to the column
                      names in the `validation_df`.
        tolerance: The relative tolerance to use when comparing floating-point
                   numbers. Defaults to 1e-3.

    Returns:
        `True` if all scenarios match their expected values within the given
        tolerance, `False` otherwise.
    """
    logging.info("--- DSA Validation Summary ---")
    total_scenarios = len(dsa_results)
    matched_scenarios = 0
    all_passed = True

    for scenario_name, result_df in dsa_results.items():
        validation_col = scenario_map.get(scenario_name)
        if not validation_col or validation_col not in validation_df.columns:
            logging.warning(f"Scenario '{scenario_name}' not found in validation map.")
            continue

        # If 'Personnel type' exists, align on that; otherwise compare by row order
        if (
            "Personnel type" in validation_df.columns
            and "Personnel type" in result_df.columns
        ):
            comparison_df = pd.merge(
                result_df,
                validation_df[["Personnel type", validation_col]],
                on="Personnel type",
                how="inner",
            )
            calculated_values = comparison_df["Calculated_Cost_Mid_Y0"].values
            expected_values = comparison_df[validation_col].values
        else:
            calculated_values = result_df["Calculated_Cost_Mid_Y0"].values
            expected_values = validation_df[validation_col].values[
                : len(calculated_values)
            ]

        if np.allclose(
            np.asarray(calculated_values),
            np.asarray(expected_values),
            rtol=tolerance,
            equal_nan=True,
        ):
            logging.info(f"✅ Scenario '{scenario_name}' matched successfully.")
            matched_scenarios += 1
        else:
            all_passed = False
            logging.error(f"❌ Scenario '{scenario_name}' has a discrepancy.")
            discrepancy_idx = np.where(
                ~np.isclose(
                    np.asarray(calculated_values),
                    np.asarray(expected_values),
                    rtol=tolerance,
                    equal_nan=True,
                )
            )[0]
            if discrepancy_idx.size > 0:
                idx = discrepancy_idx[0]
                calculated = calculated_values[idx]
                expected = expected_values[idx]
                diff = calculated - expected
                relative_diff = diff / expected if expected != 0 else np.inf
                logging.error(
                    f"  Example discrepancy at index {idx}: "
                    f"Calculated={calculated:,.2f}, Expected={expected:,.2f}, "
                    f"Diff={diff:,.2f} ({relative_diff:.2%})"
                )

    logging.info(f"{matched_scenarios} out of {total_scenarios} DSA scenarios matched.")
    return all_passed


def validate_psa_results(
    psa_results: pd.DataFrame,
    validation_df: pd.DataFrame,
    tolerance: float = 1e-3,
) -> bool:
    """
    Validates the PSA results against a pre-calculated expected mean cost.

    Args:
        psa_results: A DataFrame containing the results of each PSA iteration.
        validation_df: A DataFrame containing the expected mean cost for validation.
        tolerance: The relative tolerance to use for the comparison.

    Returns:
        `True` if the calculated mean cost matches the expected value within the
        given tolerance, `False` otherwise.
    """
    logging.info("--- PSA Validation Summary ---")
    if psa_results.empty:
        logging.warning("PSA results are empty. Skipping validation.")
        return True

    if "Expected Mean Cost" not in validation_df.columns:
        logging.error("'Expected Mean Cost' column not found in validation data.")
        return False

    expected_mean_cost = validation_df["Expected Mean Cost"].iloc[0]
    calculated_mean_cost = psa_results["mean_cost"].mean()

    if np.isclose(expected_mean_cost, calculated_mean_cost, rtol=tolerance):
        logging.info("✅ PSA mean cost matched successfully.")
        return True
    else:
        logging.error("❌ PSA mean cost has a discrepancy.")
        diff = calculated_mean_cost - expected_mean_cost
        relative_diff = diff / expected_mean_cost if expected_mean_cost != 0 else np.inf
        logging.error(
            f"  Calculated Mean Cost={calculated_mean_cost:,.2f}, "
            f"Expected Mean Cost={expected_mean_cost:,.2f}, "
            f"Diff={diff:,.2f} ({relative_diff:.2%})"
        )
        return False
