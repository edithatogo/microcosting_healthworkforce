# src/projection.py
"""
This module handles the projection of costs over multiple years based on
a given indexation rate.
"""

import pandas as pd


def project_costs(
    base_year_costs_df: pd.DataFrame,
    scenario_df: pd.DataFrame,
    num_years: int = 5,
) -> pd.DataFrame:
    """
    Projects costs for a specified number of years based on an indexation rate.

    Args:
        base_year_costs_df: DataFrame containing the calculated costs for Year 0.
        scenario_df: The scenario-specific DataFrame, used to get the
                     indexation rate for each row.
        num_years: The number of years to project into the future.

    Returns:
        A DataFrame with the projected costs for each year.
    """
    projected_df = base_year_costs_df.copy()
    projected_df.columns = [f"{col}_Y0" for col in projected_df.columns]

    indexation_rate = scenario_df["Grade(s)_Indexation per annum (%)"].fillna(0)

    for year in range(1, num_years + 1):
        for tier in ["LL", "Mid", "UL"]:
            prev_year_col = f"Calculated_Cost_{tier}_Y{year - 1}"
            new_year_col = f"Calculated_Cost_{tier}_Y{year}"
            projected_df[new_year_col] = projected_df[prev_year_col] * (
                1 + indexation_rate
            )

    return projected_df
