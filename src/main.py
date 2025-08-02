import argparse
from typing import Any, Dict

import numpy as np
import pandas as pd

from src.data_loader import load_and_clean_data
from src.formula_engine import apply_formulas, load_formulas
from src.projection import project_costs
from src.rate_converter import convert_annual_cost_to_rates
from src.sensitivity_analysis import load_dsa_scenarios

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
    calculated_results = run_calculation_pipeline(df, formulas_data)
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
    calculated_compare = calculated_results[list(validation_map.values())].fillna(0)
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
        comparison_df = df.join(calculated_results)
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
        full_output_row = calculated_results.iloc[[first_success_idx]]
        print(full_output_row.to_string())

    # --- 6. Run Deterministic Sensitivity Analysis (DSA) ---
    try:
        scenarios_to_run = None
        if args.dsa_scenarios:
            print(f"Loading custom scenarios from '{args.dsa_scenarios}'...")
            scenarios_to_run = load_dsa_scenarios(args.dsa_scenarios)
        else:
            dsa_scenarios_path = "data/dsa_scenarios.json"
            print(f"\nLoading DSA scenarios from '{dsa_scenarios_path}'...")
            scenarios_to_run = load_dsa_scenarios(dsa_scenarios_path)

        if not scenarios_to_run:
            print("No DSA scenarios provided. Skipping.")
        else:
            print(f"\n--- Running {len(scenarios_to_run)} DSA Scenarios ---")
            dsa_results = {}
            param_to_col_map = formulas_data["outputs"][0]["parameter_mapping"]

            for scenario in scenarios_to_run:
                scenario_name = scenario["name"]
                param_to_vary = scenario["parameter_to_vary"]
                variation = scenario["variation"]
                row_filter = scenario.get("row_filter")
                print(f"  - Running scenario: {scenario_name}")

                scenario_df = df.copy(deep=True)

                if param_to_vary not in param_to_col_map:
                    print(
                        f"Warning: Param '{param_to_vary}' not in formula mapping. Skipping."
                    )
                    continue

                column_to_vary = param_to_col_map[param_to_vary]

                if row_filter:
                    mask = pd.Series(True, index=scenario_df.index)
                    for key, value in row_filter.items():
                        mask &= scenario_df[key] == value
                else:
                    mask = pd.Series(True, index=scenario_df.index)

                if variation["type"] == "percentage":
                    scenario_df.loc[mask, column_to_vary] *= 1 + variation["value"]
                elif variation["type"] == "absolute":
                    scenario_df.loc[mask, column_to_vary] += variation["value"]
                else:
                    print(
                        f"Warning: Unknown variation type '{variation['type']}'. Skipping."
                    )
                    continue

                # Run the full calculation pipeline with the modified data
                scenario_results = run_calculation_pipeline(scenario_df, formulas_data)
                dsa_results[scenario_name] = scenario_results

            print("-------------------------------------\n")

            # --- 7. Report DSA Results ---
            print("\n--- DSA Results Summary (showing Year 0 Mid-point Cost) ---")
            base_case_cost = calculated_results["Calculated_Cost_Mid_Y0"].mean()
            print(f"Base Case Average Cost: {base_case_cost:,.2f}")

            for scenario_name, result_df in dsa_results.items():
                scenario_cost = result_df["Calculated_Cost_Mid_Y0"].mean()
                percentage_change = (
                    (scenario_cost - base_case_cost) / base_case_cost
                ) * 100
                print(
                    f"  - {scenario_name:<25} | "
                    f"Result: {scenario_cost:,.2f} | "
                    f"Change: {percentage_change:+.2f}%"
                )
            print("-----------------------------------------------------------\n")

    except Exception as e:
        print(f"Failed to run DSA: {e}")


if __name__ == "__main__":
    main()
