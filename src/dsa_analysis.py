# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
# src/dsa_analysis.py
"""Evaluate declared deterministic workforce scenarios."""

import json
import logging
from pathlib import Path
from typing import Any, cast
lazy from collections.abc import Callable

import polars as pl

from src.contracts import parameter_mapping
from src.numeric import numeric
from src.numeric import row_filter as validate_row_filter

logger = logging.getLogger(__name__)


def load_dsa_scenarios(file_path: str) -> list[dict[str, Any]]:
    """Load the DSA scenario definitions from a specified JSON file."""
    try:
        with Path(file_path).open() as f:
            scenarios = json.load(f)
        return cast("list[dict[str, Any]]", scenarios)
    except FileNotFoundError as error:
        message = f"DSA scenarios file not found at: {file_path}"
        raise FileNotFoundError(message) from error
    except json.JSONDecodeError as error:
        message = f"Invalid JSON format in DSA scenarios file: {file_path}"
        raise ValueError(message) from error


def run_dsa_analysis(
    base_case_df: pl.DataFrame,
    formulas_data: dict[str, Any],
    calculation_pipeline: Callable[[pl.DataFrame, dict[str, Any]], pl.DataFrame],
    scenarios: list[dict[str, Any]],
) -> dict[str, pl.DataFrame]:
    """Run a series of Deterministic Sensitivity Analysis scenarios."""
    dsa_results: dict[str, pl.DataFrame] = {}

    param_to_col_map = parameter_mapping(formulas_data)

    for scenario in scenarios:
        scenario_name = scenario["name"]
        if scenario_name in dsa_results:
            message = f"Duplicate DSA scenario name: {scenario_name!r}"
            raise ValueError(message)
        params_to_vary = scenario.get(
            "parameters_to_vary",
            [scenario["parameter_to_vary"]] if "parameter_to_vary" in scenario else [],
        )
        variations = scenario.get(
            "variations",
            [scenario["variation"]] if "variation" in scenario else [],
        )
        if len(params_to_vary) != len(variations):
            message = f"Scenario {scenario_name!r} needs one variation per parameter"
            raise ValueError(message)
        row_filter = validate_row_filter(scenario.get("row_filter"))
        logger.info("Running scenario: %s", scenario_name)

        scenario_df = base_case_df.clone()

        for param_to_vary, variation in zip(params_to_vary, variations, strict=True):
            if param_to_vary not in param_to_col_map:
                logger.warning(
                    "Param '%s' not in formula mapping. Skipping.",
                    param_to_vary,
                )
                continue

            column_to_vary = param_to_col_map[param_to_vary]

            mask = pl.lit(value=True)
            for key, value in row_filter.items():
                mask = mask & (pl.col(key) == value)
            if variation["type"] == "percentage":
                expr = pl.col(column_to_vary) * (1 + variation["value"])
            elif variation["type"] == "absolute":
                expr = pl.col(column_to_vary) + variation["value"]
            else:
                logger.warning(
                    "Unknown variation type %r. Skipping.",
                    variation["type"],
                )
                continue
            scenario_df = scenario_df.with_columns(
                pl.when(mask)
                .then(expr)
                .otherwise(pl.col(column_to_vary))
                .alias(column_to_vary),
            )

        derived = [
            output["name"] + "_Y0"
            for output in formulas_data.get("outputs", [])
            if "name" in output
        ]
        scenario_results = calculation_pipeline(
            scenario_df.drop(derived, strict=False),
            formulas_data,
        )
        dsa_results[scenario_name] = scenario_results

    return dsa_results


def report_dsa_results(
    dsa_results: dict[str, pl.DataFrame],
    base_case_results: pl.DataFrame,
) -> None:
    """Print a summary report of the DSA results."""
    logger.info("--- DSA Results Summary (showing Year 0 Mid-point Cost) ---")
    base_case_cost = numeric(base_case_results["Calculated_Cost_Mid_Y0"].mean())
    logger.info("Base Case Average Cost: %s", format(base_case_cost, ",.2f"))

    for scenario_name, result_df in dsa_results.items():
        scenario_cost = numeric(result_df["Calculated_Cost_Mid_Y0"].mean())
        percentage_change = ((scenario_cost - base_case_cost) / base_case_cost) * 100
        logger.info(
            "  - %s | Result: %s | Change: %s%%",
            format(scenario_name, "<25"),
            format(scenario_cost, ",.2f"),
            format(percentage_change, "+.2f"),
        )
