# src/data_loader.py
"""
This module handles loading and cleaning data from the Excel file.
"""

import pandas as pd


def _clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and standardizes the column names of a DataFrame.

    This function performs several cleaning steps:
    - Joins multi-level columns into a single string.
    - Removes "Unnamed" parts from column names.
    - Replaces "(hourly)" with "_hourly".
    - Replaces spaces with underscores.
    - Replaces multiple underscores with a single underscore.
    - Corrects a specific issue with "Leave Loading (%)".
    - Removes "_nan" suffixes.

    Args:
        df: The DataFrame with dirty column names.

    Returns:
        The DataFrame with cleaned column names.
    """
    # Clean up the multi-level column names into a single string
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ["_".join(map(str, col)).strip() for col in df.columns]

    # Clean the column names by removing unwanted characters and patterns
    df.columns = (
        df.columns.str.replace(r"Unnamed: \d+_level_\d+", "", regex=True)
        .str.replace(r"_\(hourly\)", "_hourly", regex=True)
        .str.replace(r"_\s+", "_", regex=True)
        .str.replace(r"_+", "_", regex=True)
        .str.replace(r"Leave Loading \(%\)__", "Leave Loading (%)", regex=False)
        .str.replace(r"_nan", "", regex=False)
    )
    return df


def load_and_clean_data(file_path: str, sheet_name: str) -> pd.DataFrame:
    """
    Loads and cleans the primary data from the 'Labour - Prices' sheet.
    """
    # Load the sheet, skipping the top rows and setting the header
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=[1, 2])
    df = _clean_column_names(df)

    # Rename the main columns for easier access
    df.rename(
        columns={
            "Jurisdiction_": "Jurisdiction",
            "Personnel type_": "Personnel type",
        },
        inplace=True,
    )

    # Forward-fill the 'Jurisdiction' and 'Personnel type' columns
    if "Jurisdiction" in df.columns:
        df["Jurisdiction"] = df["Jurisdiction"].ffill()
    if "Personnel type" in df.columns:
        df["Personnel type"] = df["Personnel type"].ffill()

    # Drop rows where 'Personnel type' is still NaN (e.g., empty spacer rows)
    if "Personnel type" in df.columns:
        df.dropna(subset=["Personnel type"], inplace=True)

    numeric_cols = [
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
    for i in range(1, 5):
        numeric_cols.extend(
            [
                f"Base Salary_LL.{i}",
                f"Base Salary_Mid-point.{i}",
                f"Base Salary_UL.{i}",
                f"Base Salary + Costs_LL.{i}",
                f"Base Salary + Costs_Mid-point.{i}",
                f"Base Salary + Costs_UL.{i}",
                f"Base Salary + Costs (hourly)_LL.{i}",
                f"Base Salary + Costs (hourly)_Mid-point.{i}",
                f"Base Salary + Costs (hourly)_UL.{i}",
            ]
        )

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


def load_dsa_validation_data(file_path: str, sheet_name: str) -> pd.DataFrame:
    """
    Loads and cleans the DSA validation data from the specified sheet.
    """
    # Load the sheet with a multi-level header
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=[0, 1, 2])
    df = _clean_column_names(df)

    # Rename the personnel type column for easier access
    df.rename(
        columns={"Jurisdiction_Personnel type_LL": "Personnel type_"},
        inplace=True,
    )

    # Forward-fill the 'Personnel type' column
    if "Personnel type_" in df.columns:
        df["Personnel type_"] = df["Personnel type_"].ffill()

    # Rename the main columns for easier access
    df.rename(
        columns={
            "Jurisdiction_": "Jurisdiction",
            "Personnel type_": "Personnel type",
        },
        inplace=True,
    )

    # Drop rows where 'Personnel type' is still NaN
    if "Personnel type" in df.columns:
        df.dropna(subset=["Personnel type"], inplace=True)

    return df
