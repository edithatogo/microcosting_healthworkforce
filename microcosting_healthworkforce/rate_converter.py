# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Time-based rates from projected annual costs, retaining the legacy call signature."""

lazy import polars as pl

from .polars_rates import annual_to_rates


def convert_annual_cost_to_rates(
    projected_costs_df: pl.DataFrame,
    scenario_df: pl.DataFrame,
) -> pl.DataFrame:
    """Convert aligned annual cost scenarios to named period rates."""
    costs = [c for c in projected_costs_df.columns if c.startswith("Calculated_Cost_")]
    hours = "Grade(s)_Hours per week"
    inputs = [
        hours,
        *(
            c
            for c in scenario_df.columns
            if c.startswith("Base Salary + Costs (hourly)_")
        ),
    ]
    values = projected_costs_df.select(costs)
    conditions = scenario_df.select(inputs)
    if values.height != conditions.height:
        message = "Scenario rows must align with projected costs"
        raise ValueError(message)
    frame = annual_to_rates(values.hstack(conditions))
    added = frame.select(c for c in frame.columns if c not in costs and c not in inputs)

    return projected_costs_df.with_columns(added)
