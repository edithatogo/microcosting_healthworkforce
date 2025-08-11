"""
Main script for the Microcosting Health Workforce project.

This script serves as the main entry point for running the microcosting model.
It orchestrates the entire workflow, including:
- Parsing command-line arguments.
- Loading and cleaning the input data and formula definitions.
- Running the base case calculation pipeline.
- Validating the base case results against the original Excel file.
- Running Deterministic and Probabilistic Sensitivity Analyses (DSA & PSA).
- Saving all results to CSV files and generating plots.

The script is designed to be run from the command line and provides several
options for customizing the analysis, such as specifying custom DSA scenarios,
enabling PSA, and defining an output directory.

Usage:
    python src/main.py [--dsa-scenarios <path>] [--run-psa] [--output-dir <path>]
"""

import argparse
import logging
import sys
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

from src import config
from src.calculations import run_calculation_pipeline
from src.data_loader import (
    load_and_clean_data,
    load_dsa_validation_data,
)
from src.dsa_analysis import (
    load_dsa_scenarios,
    report_dsa_results,
    run_dsa_analysis,
)
from src.formula_engine import load_formulas
from src.psa_analysis import (
    load_psa_scenarios,
    report_psa_results,
    run_psa_analysis,
)
from src.reporting import save_base_case_results, save_dsa_results, save_psa_results
from src.validation import validate_dsa_results


def _setup_arg_parser() -> argparse.ArgumentParser:
    """
    Sets up the argument parser for the command-line interface.

    This function defines the command-line arguments that the script can accept,
    including options for running different types of analyses and specifying
    input/output paths.

    Returns:
        An `argparse.ArgumentParser` instance configured with all the command-line
        arguments for the application.
    """
    parser = argparse.ArgumentParser(
        description="Data-driven calculation engine for health workforce microcosting."
    )
    parser.add_argument(
        "--dsa-scenarios",
        type=str,
        help="Path to a custom JSON file with DSA scenarios.",
    )
    parser.add_argument(
        "--run-psa",
        action="store_true",
        help="Run the Probabilistic Sensitivity Analysis (PSA).",
    )
    parser.add_argument(
        "--psa-iterations",
        type=int,
        default=1000,
        help="Number of iterations for the PSA.",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Enable profiling to measure code execution performance.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=".",
        help="Directory to save output files (CSVs and plots).",
    )
    parser.add_argument(
        "--no-dsa-validation",
        action="store_true",
        help="Disable the validation of DSA results against the Excel file.",
    )
    return parser


def _load_data() -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Loads all necessary data and formula definitions from their configured paths.

    This function orchestrates the loading of three key pieces of data:
    1. The main dataset from the "Labour - Prices" sheet.
    2. The validation dataset for DSA from the "Labour - Prices (DSA, Values)" sheet.
    3. The formula definitions from the `formulas.json` file.

    It centralizes the data loading process and includes error handling to ensure
    that the application exits gracefully if any file is not found or is malformed.

    Returns:
        A tuple containing the following loaded and cleaned data:
        - df (pd.DataFrame): The main DataFrame with cleaned labour cost data.
        - dsa_validation_df (pd.DataFrame): The DataFrame for DSA validation.
        - formulas_data (dict): The dictionary of formula definitions.

    Raises:
        SystemExit: If any of the required files cannot be loaded or parsed.
    """
    logging.info("Loading and cleaning data...")
    try:
        df = load_and_clean_data(config.DATA_FILE_PATH, config.LABOUR_PRICES_SHEET)
        dsa_validation_df = load_dsa_validation_data(
            config.DATA_FILE_PATH, config.DSA_VALIDATION_SHEET
        )
        logging.info("Data loaded successfully.")
    except Exception as e:
        logging.error(f"Failed to load data: {e}")
        sys.exit(1)

    logging.info(f"Loading formulas from '{config.FORMULAS_FILE_PATH}'...")
    try:
        formulas_data = load_formulas(config.FORMULAS_FILE_PATH)
        logging.info("Formulas loaded successfully.")
    except Exception as e:
        logging.error(f"Failed to load formulas: {e}")
        sys.exit(1)

    return df, dsa_validation_df, formulas_data


def _run_base_case_and_validate(
    df: pd.DataFrame, formulas_data: Dict[str, Any]
) -> pd.DataFrame:
    """
    Runs the base case calculation and validates the results against the original data.

    This function first runs the main calculation pipeline to generate the base case
    results. It then compares these results against the corresponding values in the
    original Excel file to ensure the calculations are accurate within a defined
    tolerance. A summary of the validation is logged, and if discrepancies are
    found, the first mismatched row is reported for debugging.

    Args:
        df: The main input DataFrame containing the original data.
        formulas_data: The dictionary of formula definitions.

    Returns:
        A DataFrame containing the full, validated results of the base case
        calculation, including projections and rate conversions.
    """
    logging.info("Running base case calculation pipeline...")
    base_case_results = run_calculation_pipeline(df, formulas_data)
    logging.info("Base case calculation complete.")

    logging.info("Validating base year (Y0) results...")
    validation_map = {
        "Base Salary + Costs_LL": "Calculated_Cost_LL_Y0",
        "Base Salary + Costs_Mid-point": "Calculated_Cost_Mid_Y0",
        "Base Salary + Costs_UL": "Calculated_Cost_UL_Y0",
        "Base Salary + Costs (hourly)_LL": "Calculated_Hourly_LL_Y0",
        "Base Salary + Costs (hourly)_Mid-point": "Calculated_Hourly_Mid_Y0",
        "Base Salary + Costs (hourly)_UL": "Calculated_Hourly_UL_Y0",
    }
    df_original_compare = df[list(validation_map.keys())].fillna(0)
    calculated_compare = base_case_results[list(validation_map.values())].fillna(0)
    are_close = np.isclose(
        df_original_compare.values,
        calculated_compare.values,
        rtol=1e-03,
        equal_nan=True,
    )
    all_match = are_close.all()

    successful_rows = np.all(are_close, axis=1)
    num_successful = successful_rows.sum()
    total_rows = len(df)
    logging.info(
        f"--- Validation Summary ---\n{num_successful} out of {total_rows} "
        "rows matched successfully."
    )

    if not all_match:
        logging.warning("A discrepancy was found. Reporting the first failed row.")
        first_mismatch_idx = successful_rows.argmin()
        mismatched_row = base_case_results.iloc[[first_mismatch_idx]]
        display_cols = (
            ["Personnel type"]
            + list(validation_map.keys())
            + list(validation_map.values())
        )
        logging.warning(mismatched_row[display_cols].to_string())
    else:
        logging.info(
            "All validated values match the original Excel values within tolerance."
        )

    if num_successful > 0:
        logging.info("--- Example of Full Projected Output for a Matched Row ---")
        first_success_idx = successful_rows.argmax()
        full_output_row = base_case_results.iloc[[first_success_idx]]
        logging.info(full_output_row.to_string())

    return base_case_results


def _run_dsa(
    args: argparse.Namespace,
    df: pd.DataFrame,
    formulas_data: Dict[str, Any],
    base_case_results: pd.DataFrame,
    dsa_validation_df: pd.DataFrame,
) -> bool:
    """
    Runs the Deterministic Sensitivity Analysis (DSA).

    This function loads the DSA scenarios, runs the analysis for each one,
    reports the results, and saves the output to files. It also triggers the
    validation of the DSA results against the pre-calculated values in the
    Excel file, unless disabled by a command-line argument.

    Args:
        args: The command-line arguments from `argparse`.
        df: The main input DataFrame.
        formulas_data: The dictionary of formula definitions.
        base_case_results: The DataFrame containing the results of the base case.
        dsa_validation_df: The DataFrame for DSA validation.

    Returns:
        `True` if the DSA validation passes or is skipped, `False` otherwise.
    """
    validation_passed = True
    try:
        scenarios_path = args.dsa_scenarios or config.DSA_SCENARIOS_FILE_PATH
        logging.info(f"Loading DSA scenarios from '{scenarios_path}'...")
        scenarios_to_run = load_dsa_scenarios(scenarios_path)

        if not scenarios_to_run:
            logging.info("No DSA scenarios provided. Skipping.")
        else:
            logging.info(f"--- Running {len(scenarios_to_run)} DSA Scenarios ---")
            dsa_results = run_dsa_analysis(
                base_case_df=base_case_results,
                formulas_data=formulas_data,
                calculation_pipeline=run_calculation_pipeline,
                scenarios=scenarios_to_run,
            )
            report_dsa_results(
                dsa_results,
                base_case_results,
            )
            if args.output_dir:
                save_dsa_results(dsa_results, base_case_results, args.output_dir)
            if not args.no_dsa_validation:
                if not validate_dsa_results(
                    dsa_results,
                    dsa_validation_df,
                    config.DSA_SCENARIO_VALIDATION_MAPPING,
                ):
                    validation_passed = False
    except Exception as e:
        logging.error(f"Failed to run DSA: {e}")
        validation_passed = False
    return validation_passed


def _run_psa(
    args: argparse.Namespace,
    base_case_results: pd.DataFrame,
    formulas_data: Dict[str, Any],
) -> None:
    """
    Runs the Probabilistic Sensitivity Analysis (PSA) if requested.

    This function checks the command-line arguments to see if a PSA should be run.
    If so, it loads the PSA scenarios, runs the Monte Carlo simulation, reports
    the summary statistics, and saves the results to a file.

    Args:
        args: The command-line arguments from `argparse`.
        base_case_results: The DataFrame containing the results of the base case.
        formulas_data: The dictionary of formula definitions.
    """
    if not args.run_psa:
        return

    try:
        psa_scenarios_path = config.PSA_SCENARIOS_FILE_PATH
        logging.info(f"Loading PSA scenarios from '{psa_scenarios_path}'...")
        psa_scenarios = load_psa_scenarios(psa_scenarios_path)

        if not psa_scenarios:
            logging.info("No PSA scenarios provided. Skipping.")
        else:
            psa_results = run_psa_analysis(
                base_case_df=base_case_results,
                formulas_data=formulas_data,
                calculation_pipeline=run_calculation_pipeline,
                scenarios=psa_scenarios,
                iterations=args.psa_iterations,
            )
            report_psa_results(psa_results)
            if args.output_dir:
                save_psa_results(psa_results, args.output_dir)
    except Exception as e:
        logging.error(f"Failed to run PSA: {e}")


def main() -> None:
    """
    Main entry point for the microcosting calculation engine.

    This function orchestrates the entire process:
    1. Sets up logging.
    2. Parses command-line arguments.
    3. Optionally enables profiling.
    4. Loads all required data.
    5. Runs and validates the base case.
    6. Runs DSA and PSA if requested.
    7. Reports validation status and exits.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )

    parser = _setup_arg_parser()
    args = parser.parse_args()

    if args.profile:
        import cProfile
        import pstats

        profiler = cProfile.Profile()
        profiler.enable()

    df, dsa_validation_df, formulas_data = _load_data()
    base_case_results = _run_base_case_and_validate(df, formulas_data)

    if args.output_dir:
        save_base_case_results(base_case_results, args.output_dir)

    dsa_validation_passed = _run_dsa(
        args, df, formulas_data, base_case_results, dsa_validation_df
    )
    _run_psa(
        args,
        base_case_results,
        formulas_data,
    )

    if args.profile:
        profiler.disable()
        stats = pstats.Stats(profiler).sort_stats("cumulative")
        stats.print_stats()

    if not dsa_validation_passed:
        logging.error("Validation failed. Exiting with status 1.")
        sys.exit(1)
    else:
        logging.info("All validations passed successfully.")


if __name__ == "__main__":
    main()
