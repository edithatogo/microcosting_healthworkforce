# tests/test_calculations.py
"""
Tests for the calculations module.
"""

import pandas as pd

from src.calculations import run_calculation_pipeline
from src.formula_engine import load_formulas


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
            "Grade(s)_Superannuation Rate (%)": [0.1],
            "Grade(s)_Hours per week": [40],
            "Grade(s)_Average Penalties %": [0.1],
            "Grade(s)_Public Holiday Penalty %": [0.1],
            "Grade(s)_Private Practice Loading %": [0.1],
            "Grade(s)_Attraction and Retention Allowance %": [0.1],
            "Grade(s)_Sick Leave %": [0.1],
            "Grade(s)_Professional Development Allowance ($)": [500],
            "Grade(s)_Annual Leave Entitlement (Weeks)": [4],
            "Grade(s)_Annual Leave Loading (%)": [0.175],
            "Grade(s)_Average productive time (%)": [0.8],
            "Grade(s)_Indexation per annum (%)": [0.02],
        }
    )
    formulas_data = load_formulas("data/formulas.json")
    result_df = run_calculation_pipeline(input_df, formulas_data)
    assert "Calculated_Cost_LL_Y0" in result_df.columns
    assert "Calculated_Cost_Mid_Y0" in result_df.columns
    assert "Calculated_Cost_UL_Y0" in result_df.columns
    assert "Calculated_Cost_LL_Y1" in result_df.columns
    assert "Calculated_Hourly_LL_Y0" in result_df.columns
    assert "Calculated_Hourly_LL_Y1" in result_df.columns
