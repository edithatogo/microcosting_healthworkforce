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
