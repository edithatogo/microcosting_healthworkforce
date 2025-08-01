import numpy as np

from src.data_loader import load_and_clean_data
from src.formula_engine import apply_formulas, load_formulas


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

    # --- 2. Run Calculation Engine ---
    print("Applying formulas using the new engine...")
    calculated_results = apply_formulas(df, formulas_data)

    # --- 3. Calculate Hourly Rates (Temporary) ---
    # This logic will also be moved to the formula engine in the future.
    print("Calculating hourly rates...")
    total_annual_hours = df["Grade(s)_Hours per week"] * 52
    # Avoid division by zero
    total_annual_hours = total_annual_hours.replace(0, np.nan)

    calculated_results["Calculated_Hourly_LL"] = (
        calculated_results["Calculated_Cost_LL"] / total_annual_hours
    )
    calculated_results["Calculated_Hourly_Mid"] = (
        calculated_results["Calculated_Cost_Mid"] / total_annual_hours
    )
    calculated_results["Calculated_Hourly_UL"] = (
        calculated_results["Calculated_Cost_UL"] / total_annual_hours
    )

    # Handle hardcoded overrides for hourly rates
    calculated_results["Calculated_Hourly_LL"] = calculated_results[
        "Calculated_Hourly_LL"
    ].fillna(df["Base Salary + Costs (hourly)_LL"])
    calculated_results["Calculated_Hourly_Mid"] = calculated_results[
        "Calculated_Hourly_Mid"
    ].fillna(df["Base Salary + Costs (hourly)_Mid-point"])
    calculated_results["Calculated_Hourly_UL"] = calculated_results[
        "Calculated_Hourly_UL"
    ].fillna(df["Base Salary + Costs (hourly)_UL"])

    # --- 4. Validate Results ---
    print("Validating results...")

    comparison_map = {
        "Base Salary + Costs_LL": "Calculated_Cost_LL",
        "Base Salary + Costs_Mid-point": "Calculated_Cost_Mid",
        "Base Salary + Costs_UL": "Calculated_Cost_UL",
        "Base Salary + Costs (hourly)_LL": "Calculated_Hourly_LL",
        "Base Salary + Costs (hourly)_Mid-point": "Calculated_Hourly_Mid",
        "Base Salary + Costs (hourly)_UL": "Calculated_Hourly_UL",
    }

    # Prepare data for comparison
    df_original_compare = df[list(comparison_map.keys())].fillna(0)
    calculated_compare = calculated_results[list(comparison_map.values())].fillna(0)

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
        display_cols = (
            ["Personnel type"]
            + list(comparison_map.keys())
            + list(comparison_map.values())
        )
        print(mismatched_row[display_cols].to_string())
    else:
        print(
            "\n✅ All calculated values match the original Excel values "
            "within tolerance."
        )


if __name__ == "__main__":
    main()
