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
from src.validation import validate_dsa_results


def _setup_arg_parser() -> argparse.ArgumentParser:
    """
    Sets up the argument parser for the command-line interface.

    Returns:
        An argparse.ArgumentParser instance.
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
        help="Enable profiling.",
    )
    return parser


def _load_data() -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Loads all necessary data and formulas from the configured file paths.

    This function handles the loading of the main dataset, the DSA validation data,
    and the formula definitions. It will exit the program if any file fails to load.

    Returns:
        A tuple containing:
        - df (pd.DataFrame): The main cleaned DataFrame.
        - dsa_validation_df (pd.DataFrame): The DataFrame for DSA validation.
        - formulas_data (dict): The dictionary of formula definitions.
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

    Args:
        df (pd.DataFrame): The main input DataFrame.
        formulas_data (dict): The dictionary of formula definitions.

    Returns:
        A pd.DataFrame containing the results of the base case calculation.
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
        comparison_df = df.join(base_case_results)
        mismatched_row = comparison_df.iloc[[first_mismatch_idx]]
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
    Runs the Deterministic Sensitivity Analysis based on provided scenarios.

    Args:
        args: The command-line arguments.
        df (pd.DataFrame): The main input DataFrame.
        formulas_data (dict): The dictionary of formula definitions.
        base_case_results (pd.DataFrame): The results of the base case calculation.
        dsa_validation_df (pd.DataFrame): The DataFrame for DSA validation.

    Returns:
        A boolean indicating if the DSA validation passed.
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
                base_case_df=df,
                formulas_data=formulas_data,
                calculation_pipeline=run_calculation_pipeline,
                scenarios=scenarios_to_run,
            )
            report_dsa_results(dsa_results, base_case_results)
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
    args: argparse.Namespace, df: pd.DataFrame, formulas_data: Dict[str, Any]
) -> None:
    """
    Runs the Probabilistic Sensitivity Analysis if requested.

    Args:
        args: The command-line arguments.
        df (pd.DataFrame): The main input DataFrame.
        formulas_data (dict): The dictionary of formula definitions.
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
                base_case_df=df,
                formulas_data=formulas_data,
                calculation_pipeline=run_calculation_pipeline,
                scenarios=psa_scenarios,
                iterations=args.psa_iterations,
            )
            report_psa_results(psa_results)
    except Exception as e:
        logging.error(f"Failed to run PSA: {e}")


def main() -> None:
    """
    Main function to run the data-driven calculation engine and validate results.
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

    dsa_validation_passed = _run_dsa(
        args, df, formulas_data, base_case_results, dsa_validation_df
    )
    _run_psa(args, df, formulas_data)

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
