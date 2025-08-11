# src/calculations.py
"""
This module contains the core calculation pipeline, which orchestrates the
sequence of operations to transform the input data into the final, fully-costed
and projected results.
"""

from typing import Any

import pandas as pd

from src import config
from src.formula_engine import apply_formulas
from src.projection import project_costs
from src.rate_converter import convert_annual_cost_to_rates


def run_calculation_pipeline(
    input_df: pd.DataFrame,
    formulas_data: dict[str, Any],
) -> pd.DataFrame:
    """
    Runs the full calculation pipeline on a given DataFrame.

    This function serves as the main orchestrator for the calculation process,
    sequentially calling the necessary functions to perform:
    1.  **Base Year Calculation:** Applies the data-driven formulas to the input
        data to calculate the costs for the base year (Year 0).
    2.  **Cost Projection:** Projects the calculated base year costs into the
        future for a specified number of years using an indexation rate.
    3.  **Rate Conversion:** Converts the final annual costs for all years into
        more granular rates (e.g., hourly, daily, weekly).

    Args:
        input_df: The DataFrame with the input data, which can be either the
                  base case data or a modified version for a sensitivity
                  analysis scenario.
        formulas_data: The dictionary of formula definitions loaded from the
                       JSON configuration.

    Returns:
        A DataFrame containing the final, fully calculated results, including
        projections and all converted rates.
    """
    # 1. Calculate base year costs
    base_year_costs_df = apply_formulas(input_df, formulas_data)

    # 2. Project costs for future years
    projected_costs_df = project_costs(
        base_year_costs_df, base_year_costs_df, num_years=config.PROJECTION_YEARS
    )

    # 3. Convert all annual costs to rates
    final_df = convert_annual_cost_to_rates(projected_costs_df, base_year_costs_df)

    # 4. Return the final results
    return final_df
