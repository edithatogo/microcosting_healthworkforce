# src/reporting.py
"""
This module handles the generation of all file-based outputs for the model.

It includes functions to save tabular data (like base case results, DSA, and
PSA) to CSV files, as well as functions to generate and save visualizations
such as tornado plots for DSA and histograms for PSA. This centralizes all
file I/O for reporting, making it easier to manage output formats and paths.
"""

import logging
import os
from typing import Dict

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def save_base_case_results(base_case_results: pd.DataFrame, output_dir: str) -> None:
    """
    Saves the full base case results to a CSV file.

    Args:
        base_case_results: A DataFrame containing the complete results of the
                           base case calculation, including all projections
                           and rate conversions.
        output_dir: The directory where the output file will be saved. The
                    file will be named 'base_case_results.csv'.
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
    Saves the Deterministic Sensitivity Analysis (DSA) results to CSV files.

    This function saves two types of outputs:
    1.  **Detailed Results:** A separate CSV file for each scenario is saved in a
        'dsa_detailed' subdirectory.
    2.  **Summary Results:** A single CSV file summarizing the impact of each
        scenario compared to the base case.
    It also triggers the generation of the DSA tornado plot.

    Args:
        dsa_results: A dictionary where keys are scenario names and values are
                     the corresponding result DataFrames.
        base_case_results: The DataFrame of the base case results, used for
                           comparison in the summary.
        output_dir: The base directory for saving the outputs.
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
    Saves the Probabilistic Sensitivity Analysis (PSA) results to a CSV file.

    This function saves the raw results of each iteration of the Monte Carlo
    simulation. It also triggers the generation of the PSA histogram plot.

    Args:
        psa_results: A DataFrame containing the results of each PSA iteration.
        output_dir: The directory where the output file will be saved. The
                    file will be named 'psa_results.csv'.
    """
    output_path = os.path.join(output_dir, "psa_results.csv")
    try:
        psa_results.to_csv(output_path, index=False)
        logging.info(f"PSA results saved to {output_path}")
    except Exception as e:
        logging.error(f"Failed to save PSA results: {e}")

    plot_psa_histogram(psa_results, output_dir)


def plot_dsa_tornado(
    dsa_summary_df: pd.DataFrame,
    output_dir: str,
) -> None:
    """
    Generates and saves a tornado plot for the DSA results.

    A tornado plot is a visualization that helps to compare the relative
    importance of different variables. In this context, it shows how sensitive
    the final cost is to changes in different input parameters.

    Args:
        dsa_summary_df: A DataFrame containing the summary of the DSA results,
                        including the percentage change for each scenario.
        output_dir: The directory where the plot will be saved. The file will
                    be named 'dsa_tornado_plot.png'.
    """
    plt.figure(figsize=(10, 8))
    # Assign hue to the same variable as y to use a palette without triggering
    # seaborn's deprecation (palette requires hue in seaborn >=0.14).
    sns.barplot(
        x="percentage_change",
        y="scenario_name",
        data=dsa_summary_df.sort_values("percentage_change", ascending=False),
        hue="scenario_name",
        palette="vlag",
        legend=False,
        dodge=False,
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


def plot_psa_histogram(psa_results_df: pd.DataFrame, output_dir: str) -> None:
    """
    Generates and saves a histogram of the PSA simulation results.

    This plot shows the distribution of the mean cost from the Monte Carlo
    simulation, providing insight into the uncertainty of the final cost estimate.

    Args:
        psa_results_df: A DataFrame containing the results of each PSA iteration.
        output_dir: The directory where the plot will be saved. The file will
                    be named 'psa_histogram.png'.
    """
    plt.figure(figsize=(10, 6))
    sns.histplot(psa_results_df["mean_cost"], kde=True)
    plt.xlabel("Mean Cost")
    plt.ylabel("Frequency")
    plt.title("PSA Results Distribution")
    plt.tight_layout()
    output_path = os.path.join(output_dir, "psa_histogram.png")
    try:
        plt.savefig(output_path)
        logging.info(f"PSA histogram saved to {output_path}")
    except Exception as e:
        logging.error(f"Failed to save PSA histogram: {e}")
    plt.close()
