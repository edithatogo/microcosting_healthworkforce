# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
# src/calculations.py
"""Run the annual-cost, projection and rate-conversion pipeline."""

lazy import polars as pl

from src import config
from src.formula_engine import apply_formulas
from src.projection import project_costs
from src.rate_converter import convert_annual_cost_to_rates


def run_calculation_pipeline(
    input_df: pl.DataFrame,
    formulas_data: object,
) -> pl.DataFrame:
    """Run the full calculation pipeline on a given DataFrame.

    Args:
        input_df: The DataFrame with the input data.
        formulas_data: The dictionary of formula definitions.

    Returns:
        A DataFrame with the final calculated results.

    """
    # 1. Calculate base year costs
    base_year_costs_df = apply_formulas(input_df, formulas_data)

    # 2. Project costs for future years
    projected_costs_df = project_costs(
        base_year_costs_df,
        base_year_costs_df,
        num_years=config.PROJECTION_YEARS,
    )

    # 3. Convert all annual costs to rates
    return convert_annual_cost_to_rates(projected_costs_df, base_year_costs_df)

    # 4. Return the final results
