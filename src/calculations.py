# src/calculations.py
"""
This module contains the core calculation pipeline.
"""

from typing import Any, Dict

import pandas as pd

from src.formula_engine import apply_formulas
from src.projection import project_costs
from src.rate_converter import convert_annual_cost_to_rates

PROJECTION_YEARS = 5


def run_calculation_pipeline(
    input_df: pd.DataFrame,
    formulas_data: Dict[str, Any],
) -> pd.DataFrame:
    """
    Runs the full calculation pipeline on a given DataFrame.

    Args:
        input_df: The DataFrame with the input data.
        formulas_data: The dictionary of formula definitions.

    Returns:
        A DataFrame with the final calculated results.
    """
    # --- 1. Run Calculation Engine for Base Year Annual Costs ---
    base_year_costs_df = apply_formulas(input_df, formulas_data)

    # Join the calculated costs with the original dataframe
    # Overwrite existing columns in input_df with results from base_year_costs_df
    joined_df = input_df.join(base_year_costs_df, how="left", lsuffix="_orig")

    # --- 2. Project Costs for Future Years ---
    projected_costs_df = project_costs(joined_df, joined_df, num_years=PROJECTION_YEARS)

    # --- 3. Convert All Annual Costs to Rates ---
    rates_df = convert_annual_cost_to_rates(projected_costs_df, joined_df)

    # --- 4. Combine and Return Results ---
    return projected_costs_df.join(rates_df)
