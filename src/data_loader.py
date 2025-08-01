import pandas as pd


def load_and_clean_data(file_path: str, sheet_name: str) -> pd.DataFrame:
    """
    Loads data from the specified Excel sheet, handles the multi-level headers,
    and selects only the input columns and the 'Year 0' output columns.

    Args:
        file_path: The path to the Excel file.
        sheet_name: The name of the sheet to load.

    Returns:
        A pandas DataFrame containing the cleaned and selected data.
    """
    # The headers are on rows 2 and 3 of the Excel sheet.
    # In pandas, this corresponds to header=[1, 2].
    header_rows = [1, 2]

    # Load the sheet, specifying the multi-level header.
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_rows)

    # --- Column Selection ---
    # Based on our analysis, the input columns end at "Indexation per annum (%)"
    # and the 'Year 0' calculations are the next 9 columns.

    # Get the input columns (first 21 columns of the multi-level header)
    input_columns = df.columns[:21]

    # Get the 'Year 0' columns. These are the columns from index 21 to 29.
    year_0_columns = df.columns[21:30]

    # Combine the desired columns into a single list
    selected_columns = input_columns.union(year_0_columns, sort=False)

    # Create the new DataFrame with only the selected columns
    df_selected = df[selected_columns]

    # --- Data Cleaning ---
    # 1. Clean up the multi-level column names for easier access.
    # The headers have multiple levels, like ('Base Salary', 'LL').
    # We can join them into a single string, e.g., 'Base Salary_LL'.
    new_columns = []
    for col in df_selected.columns:
        # Join the levels of the multi-index with a separator
        # and clean up any "Unnamed" parts.
        level1 = str(col[0]) if "Unnamed" not in str(col[0]) else ""
        level2 = str(col[1]) if "Unnamed" not in str(col[1]) else ""

        # Create a clean, single-level name
        if level1 and level2:
            new_columns.append(f"{level1}_{level2}")
        elif level1:
            new_columns.append(level1)
        else:
            new_columns.append(level2)

    df_selected.columns = new_columns

    # 2. Remove empty rows that were used for spacing in Excel.
    # A row is considered empty if the 'Jurisdiction' column is NaN.
    df_cleaned = df_selected.dropna(subset=["Jurisdiction"]).reset_index(drop=True)

    # 3. Convert all relevant columns to numeric types, coercing errors.
    # This is crucial to prevent TypeErrors during calculations.
    numeric_cols = [
        "Grade(s)_Superannuation Rate (%)",
        "Grade(s)_Hours per week",
        "Grade(s)_Average productive time (%)",
        "Grade(s)_Average Penalties %",
        "Grade(s)_Public Holiday Penalty %",
        "Grade(s)_Private Practice Loading %",
        "Grade(s)_Attraction and Retention Allowance %",
        "Grade(s)_Sick Leave %",
        "Grade(s)_Professional Development Allowance ($)",
        "Grade(s)_Annual Leave Entitlement (Weeks)",
        "Grade(s)_Annual Leave Loading (%)",
        "Grade(s)_Indexation per annum (%)",
        "Base Salary_LL",
        "Base Salary_Mid-point",
        "Base Salary_UL",
        "Base Salary + Costs_LL",
        "Base Salary + Costs_Mid-point",
        "Base Salary + Costs_UL",
        "Base Salary + Costs (hourly)_LL",
        "Base Salary + Costs (hourly)_Mid-point",
        "Base Salary + Costs (hourly)_UL",
    ]

    for col in numeric_cols:
        if col in df_cleaned.columns:
            df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors="coerce")

    return df_cleaned


if __name__ == "__main__":
    # This block is for testing the function directly.
    file_path = "data/Labour Model - v3, 20240328.xlsx"
    sheet_name = "Labour - Prices"

    try:
        cleaned_df = load_and_clean_data(file_path, sheet_name)
        print("Successfully loaded and cleaned the data for Year 0.")
        print("Shape of the DataFrame:", cleaned_df.shape)
        print("\nColumns:")
        print(cleaned_df.columns.tolist())
        print("\nFirst 5 rows:")
        print(cleaned_df.head().to_string())
    except Exception as e:
        print(f"An error occurred: {e}")
