import numpy as np

from src.calculations import calculate_year_0_costs
from src.data_loader import load_and_clean_data


def main() -> None:
    """
    Main function to run the Excel to Python translation and validation.
    This iterates through each row and compares the Python calculation
    to the original Excel value.
    """
    # --- 1. Load Data ---
    file_path = "data/Labour Model - v3, 20240328.xlsx"
    sheet_name = "Labour - Prices"

    print("Loading and cleaning data...")
    try:
        df = load_and_clean_data(file_path, sheet_name)
        print("Data loaded successfully.")
    except Exception as e:
        print(f"Failed to load data: {e}")
        return

    # --- 2. Run Calculation ---
    print("Applying Year 0 cost calculations to each row...")
    calculated_results = df.apply(calculate_year_0_costs, axis=1)

    # --- 3. Validate Results ---
    print("Validating results...")

    comparison_map = {
        "Base Salary + Costs_LL": "Calculated_Cost_LL",
        "Base Salary + Costs_Mid-point": "Calculated_Cost_Mid",
        "Base Salary + Costs_UL": "Calculated_Cost_UL",
        "Base Salary + Costs (hourly)_LL": "Calculated_Hourly_LL",
        "Base Salary + Costs (hourly)_Mid-point": "Calculated_Hourly_Mid",
        "Base Salary + Costs (hourly)_UL": "Calculated_Hourly_UL",
    }

    # Prepare data for comparison by filling potential NaN values
    df_original_compare = df[list(comparison_map.keys())].fillna(0)
    calculated_compare = calculated_results[list(comparison_map.values())].fillna(0)

    # Use np.isclose for safe floating-point comparison (0.1% relative tolerance)
    are_close = np.isclose(
        df_original_compare.values,
        calculated_compare.values,
        rtol=1e-03,
        equal_nan=True,  # Treat NaN as equal to NaN
    )

    all_match = are_close.all()

    # --- 4. Report Summary ---
    successful_rows = np.all(are_close, axis=1)
    num_successful = successful_rows.sum()
    total_rows = len(df)

    print("\n--- Validation Summary ---")
    print(f"{num_successful} out of {total_rows} rows matched successfully.")

    if num_successful > 0:
        print("\n--- Example of a Successfully Calculated Row ---")
        # Combine original and calculated for easy comparison
        comparison_df = df.join(calculated_results)
        # Find the first successful row
        first_success_idx = successful_rows.argmax()
        successful_row = comparison_df.iloc[[first_success_idx]]
        display_cols = (
            ["Personnel type"]
            + list(comparison_map.keys())
            + list(comparison_map.values())
        )
        print(successful_row[display_cols].to_string())

    if not all_match:
        print("\n❌ A discrepancy was found. Reporting the first failed row.")

        # Find the index of the first row with any mismatch
        first_mismatch_idx = successful_rows.argmin()

        # Combine original and calculated for easy comparison
        comparison_df = df.join(calculated_results)
        mismatched_row = comparison_df.iloc[[first_mismatch_idx]]

        print("\n--- First Mismatched Row ---")
        display_cols = (
            ["Personnel type"]
            + list(comparison_map.keys())
            + list(comparison_map.values())
        )
        print(mismatched_row[display_cols].to_string())
    else:
        print(
            "\n✅ All calculated values for all rows match the original"
            " Excel values within the tolerance."
        )


if __name__ == "__main__":
    main()
