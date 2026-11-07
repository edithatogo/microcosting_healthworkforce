# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Project annual costs using the scenario's annual indexation rate."""

import polars as pl


def project_costs(
    base_year_costs_df: pl.DataFrame,
    scenario_df: pl.DataFrame,
    num_years: int = 5,
) -> pl.DataFrame:
    """Compound each tier annually. Legacy callers keep their original index."""
    column = "Grade(s)_Indexation per annum (%)"
    frame = base_year_costs_df
    rate = scenario_df[column]
    if frame.height != len(rate):
        message = "Scenario rows must align with base costs"
        raise ValueError(message)
    factor = 1 + rate.cast(pl.Float64).fill_nan(None).fill_null(0)
    for year in range(1, num_years + 1):
        frame = frame.with_columns(
            (pl.col(f"Calculated_Cost_{tier}_Y{year - 1}") * factor).alias(
                f"Calculated_Cost_{tier}_Y{year}",
            )
            for tier in ("LL", "Mid", "UL")
        )

    return frame


def project_workbook_costs(
    base_year_costs_df: pl.DataFrame,
    indexation_percent_points: pl.Series,
    fixed_annual_cost: pl.Series,
    num_years: int = 4,
) -> pl.DataFrame:
    """Replay simple salary indexation with the fixed cost already in Y0.

    The fixed cost must be on the same basis as the annual totals, including
    any productive-time adjustment. Indexation uses the stored workbook
    value as percentage points. Inputs are aligned positionally.
    """
    if (
        not len(indexation_percent_points)
        == len(fixed_annual_cost)
        == (base_year_costs_df.height)
    ):
        message = "Workbook projection rows must align"
        raise ValueError(message)
    if num_years < 0:
        message = "Projection years must be nonnegative"
        raise ValueError(message)
    rate = indexation_percent_points.cast(pl.Float64) / 100
    fixed = fixed_annual_cost.cast(pl.Float64)
    if not rate.is_finite().fill_null(value=False).all() or not (
        fixed.is_finite().fill_null(value=False).all()
    ):
        message = "Workbook projection requires finite indexation and fixed costs"
        raise ValueError(message)
    return base_year_costs_df.with_columns(
        (
            (pl.col(f"Calculated_Cost_{tier}_Y0") - fixed) * (1 + rate * year) + fixed
        ).alias(f"Calculated_Cost_{tier}_Y{year}")
        for year in range(1, num_years + 1)
        for tier in ("LL", "Mid", "UL")
    )
