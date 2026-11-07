# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Polars equivalent of the rate converter for a single aligned scenario table."""

import re

import polars as pl


def annual_to_rates(frame: pl.DataFrame) -> pl.DataFrame:
    """Derive annual, monthly, fortnightly, weekly, daily and hourly rates."""
    hours = pl.col("Grade(s)_Hours per week").cast(pl.Float64)
    annual_hours = pl.when(hours > 0).then(52 * hours)
    expressions: list[pl.Expr] = []
    for column in frame.columns:
        match = re.fullmatch(r"Calculated_Cost_(LL|Mid|UL)_(Y\d+)", column)
        if not match:
            continue
        tier, year = match.groups()
        cost = pl.col(column).cast(pl.Float64)
        hourly = (cost / annual_hours).fill_nan(None)
        override = "Base Salary + Costs (hourly)_" + (
            "Mid-point" if tier == "Mid" else tier
        )
        if year == "Y0" and override in frame.columns:
            hourly = hourly.fill_null(pl.col(override))
        for unit, rate in (
            ("Hourly", hourly),
            ("Daily", cost * 7.6 / annual_hours),
            ("Weekly", cost / 52),
            ("Fortnightly", cost / 26),
            ("Monthly", cost / 12),
        ):
            expressions.append(rate.alias(f"Calculated_{unit}_{tier}_{year}"))
    return frame.with_columns(expressions)


def productive_hourly_rates(inputs: pl.DataFrame) -> pl.DataFrame:
    """Calculate both leave-cover valuations from annual salary."""
    salary = pl.col("salary")
    loading = 1 + pl.col("loading")
    base = salary * (1 + pl.col("on_cost_fraction")) + pl.col("development")
    divisor = pl.col("productive") * 52 * pl.col("hours")
    required = (
        "salary",
        "loading",
        "on_cost_fraction",
        "development",
        "productive",
        "hours",
        "weeks",
    )
    invalid = pl.any_horizontal(
        ~pl.col(*required).cast(pl.Float64).is_finite().fill_null(value=False),
        ~divisor.is_finite(),
        divisor <= 0,
        pl.col("hours") <= 0,
        pl.col("productive") <= 0,
        pl.col("productive") > 1,
    )
    if inputs.select(invalid.any()).item():
        message = "Complete inputs and positive productive hours required"
        raise ValueError(message)
    replacement = salary * pl.col("weeks") / 52 * loading
    return inputs.with_columns(
        ((base + replacement + salary * loading) / divisor).alias("original_hourly"),
        ((base + replacement) / divisor).alias("leave_cover_only_hourly"),
    )
