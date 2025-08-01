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
    Converts calculated annual costs to hourly, daily, weekly, fortnightly,
    and monthly rates.

    Args:
        annual_costs_df: DataFrame with calculated annual costs.
        original_data_df: The original input DataFrame, used for parameters
                          like 'hours per week'.

    Returns:
        A DataFrame with all the newly calculated rate columns.
    """
    rates_df = pd.DataFrame(index=annual_costs_df.index)
    hours_per_week = original_data_df["Grade(s)_Hours per week"]

    # --- Define Divisors ---
    # Avoid division by zero by replacing 0 with NaN
    HOURS_PER_DAY = 7.6  # Standard hours in a full-time equivalent day
    work_days_per_week = (hours_per_week / HOURS_PER_DAY).replace(0, np.nan)
    total_annual_work_days = (work_days_per_week * 52).replace(0, np.nan)
    total_annual_hours = (hours_per_week * 52).replace(0, np.nan)

    # --- Calculate Rates for Each Tier (LL, Mid, UL) ---
    for tier in ["LL", "Mid", "UL"]:
        cost_col = f"Calculated_Cost_{tier}"
        annual_cost = annual_costs_df[cost_col]

        # Hourly
        hourly_col = f"Calculated_Hourly_{tier}"
        rates_df[hourly_col] = annual_cost / total_annual_hours
        # Apply hardcoded overrides for hourly rates
        override_col = f"Base Salary + Costs (hourly)_{tier}"
        if override_col in original_data_df:
            rates_df[hourly_col] = rates_df[hourly_col].fillna(
                original_data_df[override_col]
            )

        # Daily
        rates_df[f"Calculated_Daily_{tier}"] = annual_cost / total_annual_work_days

        # Weekly
        rates_df[f"Calculated_Weekly_{tier}"] = annual_cost / 52

        # Fortnightly
        rates_df[f"Calculated_Fortnightly_{tier}"] = annual_cost / 26

        # Monthly
        rates_df[f"Calculated_Monthly_{tier}"] = annual_cost / 12

    return rates_df
