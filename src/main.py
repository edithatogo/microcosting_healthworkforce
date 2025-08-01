import numpy as np

from src.data_loader import load_and_clean_data
from src.formula_engine import apply_formulas, load_formulas
from src.rate_converter import convert_annual_cost_to_rates


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

    # --- 2. Run Calculation Engine for Annual Costs ---
    print("Applying formulas to calculate annual costs...")
    annual_costs_df = apply_formulas(df, formulas_data)

    # --- 3. Convert Annual Costs to Rates ---
    print("Converting annual costs to hourly rates...")
    rates_df = convert_annual_cost_to_rates(annual_costs_df, df)

    # --- 4. Combine and Validate Results ---
    print("Validating results...")
    calculated_results = annual_costs_df.join(rates_df)

    # Define which columns to validate against the original Excel file
    validation_map = {
        "Base Salary + Costs_LL": "Calculated_Cost_LL",
        "Base Salary + Costs_Mid-point": "Calculated_Cost_Mid",
        "Base Salary + Costs_UL": "Calculated_Cost_UL",
        "Base Salary + Costs (hourly)_LL": "Calculated_Hourly_LL",
        "Base Salary + Costs (hourly)_Mid-point": "Calculated_Hourly_Mid",
        "Base Salary + Costs (hourly)_UL": "Calculated_Hourly_UL",
    }

    # Prepare data for comparison
    df_original_compare = df[list(validation_map.keys())].fillna(0)
    calculated_compare = calculated_results[list(validation_map.values())].fillna(0)

    are_close = np.isclose(
        df_original_compare.values,
        calculated_compare.values,
        rtol=1e-03,
        equal_nan=True,
    )
    all_match = are_close.all()

    # --- 5. Report Summary ---
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

        # Display only the columns that are being validated
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

    # --- 6. Display Full Results for a Sample Row (Optional) ---
    # This shows all calculated columns for the first successfully matched row
    if num_successful > 0:
        print("\n--- Example of Full Calculated Output for a Matched Row ---")
        first_success_idx = successful_rows.argmax()
        full_output_row = calculated_results.iloc[[first_success_idx]]
        print(full_output_row.to_string())


if __name__ == "__main__":
    main()
