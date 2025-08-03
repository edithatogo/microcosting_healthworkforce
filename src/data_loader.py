# src/data_loader.py
"""
This module handles loading and cleaning data from the Excel file.
"""

import re

import pandas as pd


def _clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and standardizes the column names of a DataFrame.
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
        columns={"Jurisdiction_Personnel type_LL": "Personnel type"},
        inplace=True,
    )

    # Forward-fill the 'Personnel type' column
    if "Personnel type" in df.columns and df["Personnel type"].isna().any():
        df["Personnel type"].fillna(inplace=True)

    # Drop rows where 'Personnel type' is still NaN
    df.dropna(subset=["Personnel type"], inplace=True)

    return df


