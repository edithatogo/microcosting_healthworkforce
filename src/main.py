import argparse
from typing import Any, Dict

import numpy as np
import pandas as pd

from src.data_loader import load_and_clean_data
from src.formula_engine import apply_formulas, load_formulas
from src.projection import project_costs
from src.psa import load_psa_scenarios, report_psa_results, run_psa
from src.rate_converter import convert_annual_cost_to_rates
from src.sensitivity_analysis import (
    load_dsa_scenarios,
    report_dsa_results,
    run_dsa,
)

PROJECTION_YEARS = 5


def run_calculation_pipeline(
    input_df: pd.DataFrame,
    formulas_data: Dict[str, Any],
) -> pd.DataFrame:
    """
    Runs the full calculation pipeline on a given DataFrame.

    Args:
        input_df: The DataFrame with the input data.
        formulas_data: The dictionary of formula definitions.

    Returns:
        A DataFrame with the final calculated results.
    """
    # --- 1. Run Calculation Engine for Base Year Annual Costs ---
    base_year_costs_df = apply_formulas(input_df, formulas_data)

    # Join the calculated costs with the original dataframe
    # Overwrite existing columns in input_df with results from base_year_costs_df
    joined_df = input_df.join(base_year_costs_df, how="left", lsuffix="_orig")

    # --- 2. Project Costs for Future Years ---
    projected_costs_df = project_costs(joined_df, joined_df, num_years=PROJECTION_YEARS)

    # --- 3. Convert All Annual Costs to Rates ---
    rates_df = convert_annual_cost_to_rates(projected_costs_df, joined_df)

    # --- 4. Combine and Return Results ---
    return projected_costs_df.join(rates_df)


def main() -> None:
    """
    Main function to run the data-driven calculation engine and validate results.
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
    args = parser.parse_args()

    # --- 1. Load Data and Formulas ---
    data_file_path = "data/Labour Model - v3, 20240328.xlsx"
    sheet_name = "Labour - Prices"
    formulas_file_path = "data/formulas.json"

    print("Loading and cleaning data...")
    try:
        df = load_and_clean_data(data_file_path, sheet_name)
        print("Data loaded successfully.")
    except Exception as e:
        print(f"Failed to load data: {e}")
        return

    print(f"Loading formulas from '{formulas_file_path}'...")
    try:
        formulas_data = load_formulas(formulas_file_path)
        print("Formulas loaded successfully.")
    except Exception as e:
        print(f"Failed to load formulas: {e}")
        return

    # --- 2. Run Base Case Calculation ---
    print("Running base case calculation pipeline...")
    base_case_results = run_calculation_pipeline(df, formulas_data)
    print("Base case calculation complete.")

    # --- 3. Validate Results ---
    print("\nValidating base year (Y0) results...")

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

    # --- 4. Report Summary ---
    successful_rows = np.all(are_close, axis=1)
    num_successful = successful_rows.sum()
    total_rows = len(df)

    print("\n--- Validation Summary ---")
    print(f"{num_successful} out of {total_rows} rows matched successfully.")

    if not all_match:
        print("\n❌ A discrepancy was found. Reporting the first failed row.")
        first_mismatch_idx = successful_rows.argmin()
        comparison_df = df.join(base_case_results)
        mismatched_row = comparison_df.iloc[[first_mismatch_idx]]
        display_cols = (
            ["Personnel type"]
            + list(validation_map.keys())
            + list(validation_map.values())
        )
        print(mismatched_row[display_cols].to_string())
    else:
        print(
            "\n✅ All validated values match the original Excel values "
            "within tolerance."
        )

    # --- 5. Display Full Results for a Sample Row (Optional) ---
    if num_successful > 0:
        print("\n--- Example of Full Projected Output for a Matched Row ---")
        first_success_idx = successful_rows.argmax()
        full_output_row = base_case_results.iloc[[first_success_idx]]
        print(full_output_row.to_string())

    # --- 6. Run Deterministic Sensitivity Analysis (DSA) ---
    try:
        scenarios_path = args.dsa_scenarios or "data/dsa_scenarios.json"
        print(f"\nLoading DSA scenarios from '{scenarios_path}'...")
        scenarios_to_run = load_dsa_scenarios(scenarios_path)

        if not scenarios_to_run:
            print("No DSA scenarios provided. Skipping.")
        else:
            print(f"\n--- Running {len(scenarios_to_run)} DSA Scenarios ---")
            dsa_results = run_dsa(
                base_case_df=df,
                formulas_data=formulas_data,
                calculation_pipeline=run_calculation_pipeline,
                scenarios=scenarios_to_run,
            )
            print("-------------------------------------\n")

            # --- 7. Report DSA Results ---
            report_dsa_results(dsa_results, base_case_results)

    except Exception as e:
        print(f"Failed to run DSA: {e}")

    # --- 8. Run Probabilistic Sensitivity Analysis (PSA) ---
    if args.run_psa:
        try:
            psa_scenarios_path = "data/psa_scenarios.json"
            print(f"Loading PSA scenarios from '{psa_scenarios_path}'...")
            psa_scenarios = load_psa_scenarios(psa_scenarios_path)

            if not psa_scenarios:
                print("No PSA scenarios provided. Skipping.")
            else:
                psa_results = run_psa(
                    base_case_df=df,
                    formulas_data=formulas_data,
                    calculation_pipeline=run_calculation_pipeline,
                    scenarios=psa_scenarios,
                    iterations=args.psa_iterations,
                )
                report_psa_results(psa_results)

        except Exception as e:
            print(f"Failed to run PSA: {e}")


if __name__ == "__main__":
    main()
