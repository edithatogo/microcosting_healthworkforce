# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
# src/validation.py
"""Reconcile calculated values against independent workbook references."""

import logging

import numpy as np
import polars as pl

from src.numeric import numeric

logger = logging.getLogger(__name__)


def validate_dsa_results(
    dsa_results: dict[str, pl.DataFrame],
    validation_df: pl.DataFrame,
    scenario_map: dict[str, str],
    tolerance: float = 1e-3,
) -> bool:
    """Validate the DSA results against pre-calculated values."""
    logger.info("--- DSA Validation Summary ---")
    total_scenarios = len(dsa_results)
    matched_scenarios = 0
    all_passed = True

    for scenario_name, result_df in dsa_results.items():
        validation_col = scenario_map.get(scenario_name)
        if not validation_col or validation_col not in validation_df.columns:
            logger.warning("Scenario '%s' not found in validation map.", scenario_name)
            continue

        keys = [
            k
            for k in ("Jurisdiction", "Personnel type")
            if k in validation_df.columns and k in result_df.columns
        ]
        if keys:
            if (
                result_df.select(keys).is_duplicated().any()
                or validation_df.select(keys).is_duplicated().any()
            ):
                return False
            aligned = result_df.join(
                validation_df.select(*keys, pl.col(validation_col).alias("_expected")),
                on=keys,
                validate="1:1",
            )
            if aligned.height != result_df.height:
                return False
            calculated_values = aligned["Calculated_Cost_Mid_Y0"].to_numpy()
            expected_values = aligned["_expected"].to_numpy()
        else:
            if result_df.height != validation_df.height:
                return False
            calculated_values = result_df["Calculated_Cost_Mid_Y0"].to_numpy()
            expected_values = validation_df[validation_col].to_numpy()
        if np.allclose(
            np.asarray(calculated_values),
            np.asarray(expected_values),
            rtol=tolerance,
            equal_nan=True,
        ):
            logger.info("✅ Scenario '%s' matched successfully.", scenario_name)
            matched_scenarios += 1
        else:
            all_passed = False
            logger.error("❌ Scenario '%s' has a discrepancy.", scenario_name)
            discrepancy_idx = np.where(
                ~np.isclose(
                    np.asarray(calculated_values),
                    np.asarray(expected_values),
                    rtol=tolerance,
                    equal_nan=True,
                ),
            )[0]
            if discrepancy_idx.size > 0:
                idx = discrepancy_idx[0]
                calculated = calculated_values[idx]
                expected = expected_values[idx]
                diff = calculated - expected
                relative_diff = diff / expected if expected != 0 else np.inf
                logger.error(
                    "  Example discrepancy at index %s: "
                    "Calculated=%s, Expected=%s, Diff=%s (%s)",
                    idx,
                    format(calculated, ",.2f"),
                    format(expected, ",.2f"),
                    format(diff, ",.2f"),
                    format(relative_diff, ".2%"),
                )

    logger.info(
        "%s out of %s DSA scenarios matched.",
        matched_scenarios,
        total_scenarios,
    )
    return all_passed and matched_scenarios == total_scenarios and total_scenarios > 0


def validate_psa_results(
    psa_results: pl.DataFrame,
    validation_df: pl.DataFrame,
    tolerance: float = 1e-3,
) -> bool:
    """Validate the PSA results against pre-calculated values."""
    logger.info("--- PSA Validation Summary ---")
    if psa_results.is_empty():
        logger.warning("PSA results are empty. Skipping validation.")
        return True

    if "Expected Mean Cost" not in validation_df.columns:
        logger.error("'Expected Mean Cost' column not found in validation data.")
        return False

    expected_mean_cost = validation_df["Expected Mean Cost"][0]
    calculated_mean_cost = numeric(psa_results["mean_cost"].mean())

    if np.isclose(expected_mean_cost, calculated_mean_cost, rtol=tolerance):
        logger.info("✅ PSA mean cost matched successfully.")
        return True
    logger.error("❌ PSA mean cost has a discrepancy.")
    diff = calculated_mean_cost - expected_mean_cost
    relative_diff = diff / expected_mean_cost if expected_mean_cost != 0 else np.inf
    logger.error(
        "  Calculated Mean Cost=%s, Expected Mean Cost=%s, Diff=%s (%s)",
        format(calculated_mean_cost, ",.2f"),
        format(expected_mean_cost, ",.2f"),
        format(diff, ",.2f"),
        format(relative_diff, ".2%"),
    )
    return False
