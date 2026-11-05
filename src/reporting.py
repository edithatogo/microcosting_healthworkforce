# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
# src/reporting.py
"""Save workforce result tables and statistical figures."""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl

from src.numeric import numeric

logger = logging.getLogger(__name__)


def save_base_case_results(base_case_results: pl.DataFrame, output_dir: str) -> None:
    """Save the base case results to a CSV file."""
    output_path = Path(output_dir) / "base_case_results.csv"
    try:
        base_case_results.write_csv(output_path)
        logger.info("Base case results saved to %s", output_path)
    except Exception:
        logger.exception("Failed to save base case results")


def save_dsa_results(
    dsa_results: dict[str, pl.DataFrame],
    base_case_results: pl.DataFrame,
    output_dir: str,
) -> None:
    """Save the DSA results to CSV files."""
    # Save detailed results for each scenario
    detailed_output_dir = Path(output_dir) / "dsa_detailed"
    detailed_output_dir.mkdir(parents=True, exist_ok=True)
    for scenario_name, result_df in dsa_results.items():
        output_path = Path(detailed_output_dir) / f"{scenario_name}.csv"
        try:
            result_df.write_csv(output_path)
            logger.info("DSA results for '%s' saved to %s", scenario_name, output_path)
        except Exception:
            logger.exception(
                "Failed to save DSA results for '%s'",
                scenario_name,
            )

    # Save summary results
    summary_data: list[dict[str, str | float]] = []
    base_case_cost = numeric(base_case_results["Calculated_Cost_Mid_Y0"].mean())
    for scenario_name, result_df in dsa_results.items():
        scenario_cost = numeric(result_df["Calculated_Cost_Mid_Y0"].mean())
        percentage_change = ((scenario_cost - base_case_cost) / base_case_cost) * 100
        summary_data.append(
            {
                "scenario_name": scenario_name,
                "base_case_cost": base_case_cost,
                "scenario_cost": scenario_cost,
                "percentage_change": percentage_change,
            },
        )
    summary_df = pl.DataFrame(summary_data)
    summary_output_path = Path(output_dir) / "dsa_summary.csv"
    try:
        summary_df.write_csv(summary_output_path)
        logger.info("DSA summary saved to %s", summary_output_path)
    except Exception:
        logger.exception("Failed to save DSA summary")

    plot_dsa_tornado(summary_df, output_dir)


def save_psa_results(psa_results: pl.DataFrame, output_dir: str) -> None:
    """Save the PSA results to a CSV file."""
    output_path = Path(output_dir) / "psa_results.csv"
    try:
        psa_results.write_csv(output_path)
        logger.info("PSA results saved to %s", output_path)
    except Exception:
        logger.exception("Failed to save PSA results")

    plot_psa_histogram(psa_results, output_dir)


def plot_dsa_tornado(
    dsa_summary_df: pl.DataFrame,
    output_dir: str,
) -> None:
    """Generate and saves a tornado plot for the DSA results."""
    plt.figure(figsize=(10, 8))
    # Assign hue to the same variable as y to use a palette without triggering
    # seaborn's deprecation (palette requires hue in seaborn >=0.14).
    ordered = dsa_summary_df.sort("percentage_change")
    plt.barh(ordered["scenario_name"].to_list(), ordered["percentage_change"].to_list())
    plt.xlabel("Percentage Change in Cost")
    plt.ylabel("Scenario")
    plt.title("DSA Tornado Plot")
    plt.tight_layout()
    output_path = Path(output_dir) / "dsa_tornado_plot.png"
    try:
        plt.savefig(output_path)
        logger.info("DSA tornado plot saved to %s", output_path)
    except Exception:
        logger.exception("Failed to save DSA tornado plot")
    plt.close()


def plot_psa_histogram(psa_results_df: pl.DataFrame, output_dir: str) -> None:
    """Generate and saves a histogram of the PSA results."""
    plt.figure(figsize=(10, 6))
    plt.hist(psa_results_df["mean_cost"].to_numpy())
    plt.xlabel("Mean Cost")
    plt.ylabel("Frequency")
    plt.title("PSA Results Distribution")
    plt.tight_layout()
    output_path = Path(output_dir) / "psa_histogram.png"
    try:
        plt.savefig(output_path)
        logger.info("PSA histogram saved to %s", output_path)
    except Exception:
        logger.exception("Failed to save PSA histogram")
    plt.close()
