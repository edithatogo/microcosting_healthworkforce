# src/rate_converter.py
"""
This module handles the conversion of calculated annual costs into various
time-based rates, such as hourly, daily, or weekly. This keeps the core
formula engine focused on cost composition, while this module handles
the reporting and unit conversion aspect.
"""

import numpy as np
import pandas as pd


def convert_annual_cost_to_rates(
    annual_costs_df: pd.DataFrame, original_data_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Converts the calculated annual costs to hourly rates.

    This function takes the DataFrame of calculated annual costs and the
    original input DataFrame (which contains necessary parameters like
    'hours per week') and returns a DataFrame with the calculated hourly rates.

    Args:
        annual_costs_df: DataFrame containing the calculated annual costs
                         (e.g., Calculated_Cost_LL, Calculated_Cost_Mid).
        original_data_df: The original, cleaned input DataFrame.

    Returns:
        A DataFrame with the newly calculated rate columns.
    """
    rates_df = pd.DataFrame(index=annual_costs_df.index)

    # --- Hourly Rate Calculation ---
    total_annual_hours = original_data_df["Grade(s)_Hours per week"] * 52
    # Avoid division by zero by replacing 0 with NaN
    total_annual_hours = total_annual_hours.replace(0, np.nan)

    # Calculate base hourly rates
    rates_df["Calculated_Hourly_LL"] = (
        annual_costs_df["Calculated_Cost_LL"] / total_annual_hours
    )
    rates_df["Calculated_Hourly_Mid"] = (
        annual_costs_df["Calculated_Cost_Mid"] / total_annual_hours
    )
    rates_df["Calculated_Hourly_UL"] = (
        annual_costs_df["Calculated_Cost_UL"] / total_annual_hours
    )

    # Apply hardcoded overrides from the original Excel file
    rates_df["Calculated_Hourly_LL"] = rates_df["Calculated_Hourly_LL"].fillna(
        original_data_df["Base Salary + Costs (hourly)_LL"]
    )
    rates_df["Calculated_Hourly_Mid"] = rates_df["Calculated_Hourly_Mid"].fillna(
        original_data_df["Base Salary + Costs (hourly)_Mid-point"]
    )
    rates_df["Calculated_Hourly_UL"] = rates_df["Calculated_Hourly_UL"].fillna(
        original_data_df["Base Salary + Costs (hourly)_UL"]
    )

    # (Future) --- Daily/Weekly Rate Calculation ---
    # This is where logic for other rates would be added.
    # For example:
    # total_annual_days = original_data_df["work_days_per_week"] * 52
    # rates_df["Calculated_Daily_LL"] = ...

    return rates_df
