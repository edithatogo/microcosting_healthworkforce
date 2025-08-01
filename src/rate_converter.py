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
    projected_costs_df: pd.DataFrame, original_data_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Converts projected annual costs for multiple years into hourly, daily,
    weekly, fortnightly, and monthly rates.

    Args:
        projected_costs_df: DataFrame with projected annual costs for multiple
                            years (e.g., Calculated_Cost_LL_Y0, ..._Y1).
        original_data_df: The original input DataFrame, used for parameters
                          like 'hours per week'.

    Returns:
        A DataFrame with all the newly calculated rate columns for each year.
    """
    rates_df = pd.DataFrame(index=projected_costs_df.index)
    hours_per_week = original_data_df["Grade(s)_Hours per week"]

    # --- Define Divisors ---
    # Avoid division by zero by replacing 0 with NaN
    HOURS_PER_DAY = 7.6  # Standard hours in a full-time equivalent day
    work_days_per_week = (hours_per_week / HOURS_PER_DAY).replace(0, np.nan)
    total_annual_work_days = (work_days_per_week * 52).replace(0, np.nan)
    total_annual_hours = (hours_per_week * 52).replace(0, np.nan)

    # --- Identify Years from Columns ---
    # Extracts "Y0", "Y1", etc. from the column names
    years = sorted(
        list(
            set(
                col.split("_")[-1]
                for col in projected_costs_df.columns
                if col.startswith("Calculated_Cost_")
            )
        )
    )

    # --- Calculate Rates for Each Year and Tier ---
    for year_suffix in years:  # e.g., "Y0", "Y1"
        for tier in ["LL", "Mid", "UL"]:
            cost_col = f"Calculated_Cost_{tier}_{year_suffix}"
            if cost_col not in projected_costs_df:
                continue

            annual_cost = projected_costs_df[cost_col]

            # Hourly
            hourly_col = f"Calculated_Hourly_{tier}_{year_suffix}"
            rates_df[hourly_col] = annual_cost / total_annual_hours

            # Apply hardcoded overrides for hourly rates ONLY for Year 0
            if year_suffix == "Y0":
                override_col_name = f"Base Salary + Costs (hourly)_{tier}"
                # The original sheet has "Mid-point" not "Mid"
                if tier == "Mid":
                    override_col_name = "Base Salary + Costs (hourly)_Mid-point"

                if override_col_name in original_data_df:
                    rates_df[hourly_col] = rates_df[hourly_col].fillna(
                        original_data_df[override_col_name]
                    )

            # Daily
            rates_df[f"Calculated_Daily_{tier}_{year_suffix}"] = (
                annual_cost / total_annual_work_days
            )

            # Weekly
            rates_df[f"Calculated_Weekly_{tier}_{year_suffix}"] = annual_cost / 52

            # Fortnightly
            rates_df[f"Calculated_Fortnightly_{tier}_{year_suffix}"] = annual_cost / 26

            # Monthly
            rates_df[f"Calculated_Monthly_{tier}_{year_suffix}"] = annual_cost / 12

    return rates_df
