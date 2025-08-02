# tests/test_calculations.py
"""
Tests for the calculations module.
"""

import pandas as pd

from src.calculations import run_calculation_pipeline


def test_run_calculation_pipeline() -> None:
    """
    Tests that the run_calculation_pipeline function returns a DataFrame with
    the expected columns.
    """
    input_df = pd.DataFrame(
        {
            "Personnel type": ["Test"],
            "Base Salary_LL": [100],
            "Base Salary_Mid-point": [110],
            "Base Salary_UL": [120],
            "Superannuation Rate": [0.1],
            "Grade(s)_Hours per week": [40],
            "Average Penalties": [0.1],
            "Public Holiday Penalty": [0.1],
            "Private Practice Loading": [0.1],
            "Attraction and Retention Allowance": [0.1],
            "Sick Leave": [0.1],
            "Professional Development Allowance": [0.1],
            "Annual Leave": [4],
            "Leave Loading (%)": [0.175],
            "Productive Time Factor": [0.8],
            "Grade(s)_Indexation per annum (%)": [0.02],
        }
    )
    formulas_data = {
        "formulas": [
            {
                "id": "cost_ll",
                "expression": "base_salary_ll * (1 + super_rate)",
                "parameters": ["base_salary_ll", "super_rate"],
            }
        ],
        "outputs": [
            {
                "name": "Calculated_Cost_LL_Y0",
                "uses_formula": "cost_ll",
                "parameter_mapping": {
                    "base_salary_ll": "Base Salary_LL",
                    "super_rate": "Superannuation Rate",
                },
            }
        ],
    }
    result_df = run_calculation_pipeline(input_df, formulas_data)
    assert "Calculated_Cost_LL_Y0" in result_df.columns
    assert "Calculated_Cost_LL_Y1" in result_df.columns
    assert "Calculated_Hourly_LL_Y0" in result_df.columns
    assert "Calculated_Hourly_LL_Y1" in result_df.columns
