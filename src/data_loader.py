# src/data_loader.py
"""
This module handles loading and cleaning data from the Excel file.
"""

import re

import pandas as pd


def load_and_clean_data(file_path: str, sheet_name: str) -> pd.DataFrame:
    """
    Loads and cleans the primary data from the 'Labour - Prices' sheet.
    """
    # Load the sheet, skipping the top rows and setting the header
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=[1, 2])

    df.columns = ["_".join(map(str, col)).strip() for col in df.columns]
    df.columns = pd.Index(
        [re.sub(r"Unnamed: \d+_level_\d+", "", col) for col in df.columns]
    )
    df.columns = pd.Index(
        [re.sub(r"_\(hourly\)", "_hourly", col) for col in df.columns]
    )
    df.columns = pd.Index([re.sub(r"_\s+", "_", col) for col in df.columns])
    df.columns = pd.Index([re.sub(r"_+", "_", col) for col in df.columns])
    df.columns = pd.Index(
        [
            col.replace(r"Leave Loading \(%\)__", "Leave Loading (%)")
            for col in df.columns
        ]
    )
    df.columns = pd.Index([col.replace(r"_nan", "") for col in df.columns])

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


def load_dsa_validation_data(file_path: str) -> pd.DataFrame:
    """
    Loads and cleans the DSA validation data from the
    'Labour - Prices (DSA, Values)' sheet.
    """
    # Load the sheet with a multi-level header
    df = pd.read_excel(
        file_path, sheet_name="Labour - Prices (DSA, Values)", header=[0, 1, 2]
    )

    # Clean up the multi-level column names into a single string
    df.columns = ["_".join(map(str, col)).strip() for col in df.columns]

    # Clean the column names by removing unwanted characters and patterns
    df.columns = pd.Index(
        [re.sub(r"Unnamed: \d+_level_\d+_", "", col) for col in df.columns]
    )
    df.columns = pd.Index(
        [re.sub(r"_\(hourly\)", "_hourly", col) for col in df.columns]
    )
    df.columns = pd.Index([re.sub(r"_\s+", "_", col) for col in df.columns])
    df.columns = pd.Index([re.sub(r"_+", "_", col) for col in df.columns])
    df.columns = pd.Index(
        [
            col.replace(r"Leave Loading \(%\)__", "Leave Loading (%)")
            for col in df.columns
        ]
    )

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


def get_dsa_scenario_mapping() -> dict[str, str]:
    """
    Returns a mapping from DSA scenario names to validation column names.
    """
    return {
        "Super Rate +10%": "Superannuation Rate_Base Salary + Costs_MP",
        "Super Rate -10%": "Superannuation Rate_Base Salary + Costs_MP",
        "Productive Time +5%": "Hours worked per week_Base Salary + Costs_MP",
        "Productive Time -5%": "Hours worked per week_Base Salary + Costs_MP",
        "Average Penalties +10%": "Average Penalties_Base Salary + Costs_MP",
        "Average Penalties -10%": "Average Penalties_Base Salary + Costs_MP",
        "Public Holiday Penalty +10%": "Public Holiday Penalty_Base Salary + Costs_MP",
        "Public Holiday Penalty -10%": "Public Holiday Penalty_Base Salary + Costs_MP",
        "Private Practice Loading +10%": (
            "Private Practice Loading_Base Salary + Costs_MP"
        ),
        "Private Practice Loading -10%": (
            "Private Practice Loading_Base Salary + Costs_MP"
        ),
        "Retention Allowance +10%": (
            "Attraction and Retention Allowance_Base Salary + Costs_MP"
        ),
        "Retention Allowance -10%": (
            "Attraction and Retention Allowance_Base Salary + Costs_MP"
        ),
        "Sick Leave +10%": "Sick Leave_Base Salary + Costs_MP",
        "Sick Leave -10%": "Sick Leave_Base Salary + Costs_MP",
        "Prof. Dev. Allowance +$500": (
            "Professional Development Allowance_Base Salary + Costs_MP"
        ),
        "Prof. Dev. Allowance -$500": (
            "Professional Development Allowance_Base Salary + Costs_MP"
        ),
        "Annual Leave +1 Week": "Annual Leave_Base Salary + Costs_MP",
        "Annual Leave -1 Week": "Annual Leave_Base Salary + Costs_MP",
        "Annual Leave Loading +10%": "Leave Loading (%)_Base Salary + Costs_MP",
        "Annual Leave Loading -10%": "Leave Loading (%)_Base Salary + Costs_MP",
    }
