# src/data_loader.py
"""
This module handles the loading and cleaning of data from the source Excel file.

It provides functions to load the main labour cost data, as well as the
validation data for the Deterministic and Probabilistic Sensitivity Analyses
(DSA and PSA). The cleaning functions are designed to handle the specific
formatting quirks of the original Excel file, such as multi-level headers,
inconsistent naming, and merged cells.
"""

import logging

import pandas as pd


def _clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and standardizes the column names of a DataFrame.

    This private helper function is designed to address the specific formatting
    issues found in the source Excel file's headers. It performs several
    cleaning steps to create consistent and predictable column names.

    Args:
        df: The DataFrame with potentially messy, multi-level column names.

    Returns:
        The DataFrame with a single, cleaned, and standardized header row.
    """
    # Clean up the multi-level column names into a single string
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ["_".join(map(str, col)).strip() for col in df.columns]

    # Clean the column names by removing unwanted characters and patterns
    df.columns = (
        pd.Series(df.columns)
        .str.replace(r"Unnamed: \d+_level_\d+", "", regex=True)
        .str.replace(r"_\(hourly\)", "_hourly", regex=True)
        .str.replace(r"_\s+", "_", regex=True)
        .str.replace(r"_+", "_", regex=True)
        .str.replace(r"Leave Loading \(%\)__", "Leave Loading (%)", regex=False)
        .str.replace(r"_nan", "", regex=False)
        .str.strip("_")
        .to_list()
    )
    return df


def load_and_clean_data(file_path: str, sheet_name: str) -> pd.DataFrame:
    """
    Loads and cleans the primary data from the 'Labour - Prices' sheet.

    This function reads the main dataset, handles its specific multi-level
    header, coalesces inconsistent cost columns, and performs various cleaning
    operations to prepare the data for the calculation engine.

    Args:
        file_path: The absolute path to the source Excel file.
        sheet_name: The name of the sheet to load (e.g., 'Labour - Prices').

    Returns:
        A cleaned and prepared DataFrame ready for analysis.
    """
    # Load the sheet, skipping the top rows and setting the header
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=[1, 2])
    logging.debug(f"Columns before cleaning: {df.columns}")

    # Coalesce cost columns to handle data entry inconsistencies
    df[("Base Salary + Costs", "LL")] = df[("Base Salary + Costs", "LL")].fillna(
        df[("Base Salary", "LL")]
    )
    # Coalesce Mid-point and UL, ensuring numeric types to avoid warnings
    for point in ["Mid-point", "UL"]:
        costs_col = ("Base Salary + Costs", point)
        base_col = ("Base Salary", point)

        # Ensure both columns are numeric before filling
        df[costs_col] = pd.to_numeric(df[costs_col], errors="coerce")
        df[base_col] = pd.to_numeric(df[base_col], errors="coerce")

        df[costs_col] = df[costs_col].fillna(df[base_col])

    df = _clean_column_names(df)
    logging.debug(f"Columns after cleaning: {df.columns}")

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

    This function is specifically designed to load the sheet containing the
    pre-calculated results for the DSA scenarios, which are used to validate
    the model's outputs.

    Args:
        file_path: The absolute path to the source Excel file.
        sheet_name: The name of the sheet containing DSA validation data.

    Returns:
        A cleaned DataFrame ready for use in validation checks.
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


def load_psa_validation_data(file_path: str, sheet_name: str) -> pd.DataFrame:
    """
    Loads the PSA validation data from the specified sheet.

    Args:
        file_path: The absolute path to the source Excel file.
        sheet_name: The name of the sheet containing PSA validation data.

    Returns:
        A DataFrame containing the PSA validation data.
    """
    # Load the sheet
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    return df
