from typing import Any, Dict

import numpy as np
import pandas as pd

from src.data_loader import load_and_clean_data
from src.formula_engine import apply_formulas, load_formulas
from src.projection import project_costs
from src.rate_converter import convert_annual_cost_to_rates
from src.sensitivity_analysis import load_dsa_scenarios, run_dsa

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

    # --- 2. Project Costs for Future Years ---
    projected_costs_df = project_costs(
        base_year_costs_df, input_df, num_years=PROJECTION_YEARS
    )

    # --- 3. Convert All Annual Costs to Rates ---
    rates_df = convert_annual_cost_to_rates(projected_costs_df, input_df)

    # --- 4. Combine and Return Results ---
    return projected_costs_df.join(rates_df)


def main() -> None:
    """
    Main function to run the data-driven calculation engine and validate results.
    """
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
    dsa_scenarios_path = "data/dsa_scenarios.json"
    print(f"\nLoading DSA scenarios from '{dsa_scenarios_path}'...")
    try:
        scenarios = load_dsa_scenarios(dsa_scenarios_path)

        def dsa_pipeline(
            scenario_df: pd.DataFrame, formulas: Dict[str, Any]
        ) -> pd.DataFrame:
            return run_calculation_pipeline(scenario_df, formulas)

        dsa_results = run_dsa(
            base_case_df=df,
            formulas_data=formulas_data,
            calculation_pipeline=dsa_pipeline,
            scenarios=scenarios,
        )

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

        # --- 8. Run Custom DSA with Row-level Filtering ---
        print("\n--- Running Custom DSA Scenario (with Row Filter) ---")
        custom_scenarios = [
            {
                "name": "Lab Tech Super Rate +20%",
                "parameter_to_vary": "super_rate",
                "variation": {"type": "percentage", "value": 0.20},
                "row_filter": {"Personnel type": "Lab technician"},
            },
            {
                "name": "Medical Scientist Prof. Dev. +$1000",
                "parameter_to_vary": "prof_dev_allowance",
                "variation": {"type": "absolute", "value": 1000},
                "row_filter": {"Personnel type": "Medical scientist"},
            },
        ]

        custom_dsa_results = run_dsa(
            base_case_df=df,
            formulas_data=formulas_data,
            calculation_pipeline=dsa_pipeline,
            custom_scenarios=custom_scenarios,
        )

        print("\n--- Custom DSA Results Summary ---")
        for scenario_name, result_df in custom_dsa_results.items():
            scenario_cost = result_df["Calculated_Cost_Mid_Y0"].mean()
            percentage_change = (
                (scenario_cost - base_case_cost) / base_case_cost
            ) * 100
            print(
                f"  - {scenario_name:<35} | "
                f"Result: {scenario_cost:,.2f} | "
                f"Change: {percentage_change:+.2f}%"
            )
        print("------------------------------------\n")

    except Exception as e:
        print(f"Failed to run DSA: {e}")


if __name__ == "__main__":
    main()
