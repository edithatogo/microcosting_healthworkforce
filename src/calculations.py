from typing import cast

import pandas as pd


def calculate_year_0_costs(row: pd.Series) -> pd.Series:
    """
    Calculates the 'Year 0' costs based on the logic from the Excel sheet.
    This function processes a single row (representing one worker type).

    Args:
        row: A pandas Series representing a single row from the cleaned DataFrame.

    Returns:
        A pandas Series containing the calculated costs for Year 0
        (Base Salary + Costs and Hourly Rate for LL, Mid-point, and UL).
    """
    # --- Extract Input Values from the row ---
    # Fill NaN values with 0 for all cost components, as a missing
    # cost should be treated as zero.
    base_ll = row.get("Base Salary_LL", 0)
    base_mid = row.get("Base Salary_Mid-point", 0)
    base_ul = row.get("Base Salary_UL", 0)

    super_rate = row.get("Grade(s)_Superannuation Rate (%)", 0)
    avg_penalties = row.get("Grade(s)_Average Penalties %", 0)
    pub_holiday_penalty = row.get("Grade(s)_Public Holiday Penalty %", 0)
    private_practice_loading = row.get("Grade(s)_Private Practice Loading %", 0)
    retention_allowance = row.get("Grade(s)_Attraction and Retention Allowance %", 0)
    sick_leave = row.get("Grade(s)_Sick Leave %", 0)
    prof_dev_allowance = row.get("Grade(s)_Professional Development Allowance ($)", 0)
    annual_leave_weeks = row.get("Grade(s)_Annual Leave Entitlement (Weeks)", 0)
    annual_leave_loading = row.get("Grade(s)_Annual Leave Loading (%)", 0)
    # Divisors - with guards against zero
    productive_time_factor: float = float(
        row.get("Grade(s)_Average productive time (%)", 1.0)
    )
    if productive_time_factor == 0.0:
        productive_time_factor = 1.0  # Default to 1.0 to avoid division by zero

    hours_per_week = row.get("Grade(s)_Hours per week", 0)

    # --- Define the core calculation logic as a reusable function ---
    def calculate_total_cost(base_salary: float) -> float:
        if pd.isna(base_salary) or base_salary == 0:
            return 0.0

        # Final, precise, and literal translation of the Excel formula.
        t1 = base_salary
        t2 = base_salary * super_rate
        t3 = base_salary * avg_penalties
        t4 = base_salary * pub_holiday_penalty
        t5 = base_salary * private_practice_loading
        t6 = base_salary * retention_allowance
        t7 = base_salary * sick_leave
        t8 = prof_dev_allowance
        t9 = (base_salary * ((52 + annual_leave_weeks) / 52)) * (
            1 + annual_leave_loading
        )

        total_before_prod_adj = t1 + t2 + t3 + t4 + t5 + t6 + t7 + t8 + t9
        final_cost = total_before_prod_adj / productive_time_factor
        return cast(float, final_cost)

    # --- Check for hardcoded overrides from the original Excel file ---
    # If the 'Base Salary + Costs' columns have a pre-existing numeric value,
    # it means they were hardcoded in Excel. In that case, we use the original
    # value instead of calculating it. This handles generic or averaged rows.

    original_cost_ll = row.get("Base Salary + Costs_LL")
    original_cost_mid = row.get("Base Salary + Costs_Mid-point")
    original_cost_ul = row.get("Base Salary + Costs_UL")

    # --- Apply the calculation for LL, Mid-point, and UL ---
    # Use the original value if it's a valid number, otherwise calculate it.
    cost_ll = (
        original_cost_ll
        if pd.notna(original_cost_ll) and original_cost_ll > 0
        else calculate_total_cost(base_ll)
    )
    cost_mid = (
        original_cost_mid
        if pd.notna(original_cost_mid) and original_cost_mid > 0
        else calculate_total_cost(base_mid)
    )
    cost_ul = (
        original_cost_ul
        if pd.notna(original_cost_ul) and original_cost_ul > 0
        else calculate_total_cost(base_ul)
    )

    # --- Calculate the hourly rates ---
    # Guard against division by zero for total_annual_hours
    total_annual_hours = hours_per_week * 52

    # Check for hardcoded hourly rate overrides
    original_hourly_ll = row.get("Base Salary + Costs (hourly)_LL")
    original_hourly_mid = row.get("Base Salary + Costs (hourly)_Mid-point")
    original_hourly_ul = row.get("Base Salary + Costs (hourly)_UL")

    if total_annual_hours == 0:
        hourly_ll, hourly_mid, hourly_ul = 0, 0, 0
    else:
        # Use original hourly rate if it exists, otherwise calculate it
        hourly_ll = (
            original_hourly_ll
            if pd.notna(original_hourly_ll)
            else (cost_ll / total_annual_hours)
        )
        hourly_mid = (
            original_hourly_mid
            if pd.notna(original_hourly_mid)
            else (cost_mid / total_annual_hours)
        )
        hourly_ul = (
            original_hourly_ul
            if pd.notna(original_hourly_ul)
            else (cost_ul / total_annual_hours)
        )

    # --- Return the results as a Series ---
    return pd.Series(
        {
            "Calculated_Cost_LL": cost_ll,
            "Calculated_Cost_Mid": cost_mid,
            "Calculated_Cost_UL": cost_ul,
            "Calculated_Hourly_LL": hourly_ll,
            "Calculated_Hourly_Mid": hourly_mid,
            "Calculated_Hourly_UL": hourly_ul,
        }
    )
