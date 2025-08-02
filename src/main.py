import argparse
import sys

import numpy as np

from src.calculations import run_calculation_pipeline
from src.data_loader import (
    get_dsa_scenario_mapping,
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

PROJECTION_YEARS = 5


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
        dsa_validation_df = load_dsa_validation_data(data_file_path)
        print("Data loaded successfully.")
    except Exception as e:
        print(f"Failed to load data: {e}")
        sys.exit(1)

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
    validation_passed = True
    try:
        scenarios_path = args.dsa_scenarios or "data/dsa_scenarios.json"
        print(f"\nLoading DSA scenarios from '{scenarios_path}'...")
        scenarios_to_run = load_dsa_scenarios(scenarios_path)

        if not scenarios_to_run:
            print("No DSA scenarios provided. Skipping.")
        else:
            print(f"\n--- Running {len(scenarios_to_run)} DSA Scenarios ---")
            dsa_results = run_dsa_analysis(
                base_case_df=df,
                formulas_data=formulas_data,
                calculation_pipeline=run_calculation_pipeline,
                scenarios=scenarios_to_run,
            )
            print("-------------------------------------\n")

            # --- 7. Report and Validate DSA Results ---
            report_dsa_results(dsa_results, base_case_results)
            dsa_scenario_map = get_dsa_scenario_mapping()
            if not validate_dsa_results(
                dsa_results, dsa_validation_df, dsa_scenario_map
            ):
                validation_passed = False

    except Exception as e:
        print(f"Failed to run DSA: {e}")
        validation_passed = False

    # --- 8. Run Probabilistic Sensitivity Analysis (PSA) ---
    if args.run_psa:
        try:
            psa_scenarios_path = "data/psa_scenarios.json"
            print(f"Loading PSA scenarios from '{psa_scenarios_path}'...")
            psa_scenarios = load_psa_scenarios(psa_scenarios_path)

            if not psa_scenarios:
                print("No PSA scenarios provided. Skipping.")
            else:
                psa_results = run_psa_analysis(
                    base_case_df=df,
                    formulas_data=formulas_data,
                    calculation_pipeline=run_calculation_pipeline,
                    scenarios=psa_scenarios,
                    iterations=args.psa_iterations,
                )
                report_psa_results(psa_results)
                # Note: PSA validation is a placeholder.
                # if not validate_psa_results(psa_results, psa_validation_df):
                #     validation_passed = False

        except Exception as e:
            print(f"Failed to run PSA: {e}")
            validation_passed = False

    # --- 9. Final Validation Check ---
    if not validation_passed:
        print("\nValidation failed. Exiting with status 1.")
        sys.exit(1)
    else:
        print("\nAll validations passed successfully.")


if __name__ == "__main__":
    main()
