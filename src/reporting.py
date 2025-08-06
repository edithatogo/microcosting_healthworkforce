# src/reporting.py
"""
This module handles the generation of all file-based outputs, including tables
and figures for the core simulation, DSA, and PSA results.
"""

import logging
import os
from typing import Dict

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def save_base_case_results(base_case_results: pd.DataFrame, output_dir: str) -> None:
    """
    Saves the base case results to a CSV file.
    """
    output_path = os.path.join(output_dir, "base_case_results.csv")
    try:
        base_case_results.to_csv(output_path, index=False)
        logging.info(f"Base case results saved to {output_path}")
    except Exception as e:
        logging.error(f"Failed to save base case results: {e}")


def save_dsa_results(
    dsa_results: Dict[str, pd.DataFrame],
    base_case_results: pd.DataFrame,
    output_dir: str,
) -> None:
    """
    Saves the DSA results to CSV files.
    """
    # Save detailed results for each scenario
    detailed_output_dir = os.path.join(output_dir, "dsa_detailed")
    os.makedirs(detailed_output_dir, exist_ok=True)
    for scenario_name, result_df in dsa_results.items():
        output_path = os.path.join(detailed_output_dir, f"{scenario_name}.csv")
        try:
            result_df.to_csv(output_path, index=False)
            logging.info(f"DSA results for '{scenario_name}' saved to {output_path}")
        except Exception as e:
            logging.error(f"Failed to save DSA results for '{scenario_name}': {e}")

    # Save summary results
    summary_data = []
    base_case_cost = base_case_results["Calculated_Cost_Mid_Y0"].mean()
    for scenario_name, result_df in dsa_results.items():
        scenario_cost = result_df["Calculated_Cost_Mid_Y0"].mean()
        percentage_change = ((scenario_cost - base_case_cost) / base_case_cost) * 100
        summary_data.append(
            {
                "scenario_name": scenario_name,
                "base_case_cost": base_case_cost,
                "scenario_cost": scenario_cost,
                "percentage_change": percentage_change,
            }
        )
    summary_df = pd.DataFrame(summary_data)
    summary_output_path = os.path.join(output_dir, "dsa_summary.csv")
    try:
        summary_df.to_csv(summary_output_path, index=False)
        logging.info(f"DSA summary saved to {summary_output_path}")
    except Exception as e:
        logging.error(f"Failed to save DSA summary: {e}")

    plot_dsa_tornado(summary_df, output_dir)


def save_psa_results(psa_results: pd.DataFrame, output_dir: str) -> None:
    """
    Saves the PSA results to a CSV file.
    """
    output_path = os.path.join(output_dir, "psa_results.csv")
    try:
        psa_results.to_csv(output_path, index=False)
        logging.info(f"PSA results saved to {output_path}")
    except Exception as e:
        logging.error(f"Failed to save PSA results: {e}")


def plot_dsa_tornado(
    dsa_summary_df: pd.DataFrame,
    output_dir: str,
) -> None:
    """
    Generates and saves a tornado plot for the DSA results.
    """
    plt.figure(figsize=(10, 8))
    sns.barplot(
        x="percentage_change",
        y="scenario_name",
        data=dsa_summary_df.sort_values("percentage_change", ascending=False),
        palette="vlag",
    )
    plt.xlabel("Percentage Change in Cost")
    plt.ylabel("Scenario")
    plt.title("DSA Tornado Plot")
    plt.tight_layout()
    output_path = os.path.join(output_dir, "dsa_tornado_plot.png")
    try:
        plt.savefig(output_path)
        logging.info(f"DSA tornado plot saved to {output_path}")
    except Exception as e:
        logging.error(f"Failed to save DSA tornado plot: {e}")
    plt.close()
