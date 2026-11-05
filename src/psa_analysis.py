# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
# src/psa_analysis.py
"""Simulate workforce costs using declared parameter distributions."""

import json
import logging
from pathlib import Path
from typing import Any, NotRequired, TypedDict, Unpack, cast
lazy from collections.abc import Callable

import numpy as np
import polars as pl
from pydantic import ConfigDict, TypeAdapter, with_config

from src.contracts import parameter_mapping
from src.numeric import numeric

logger = logging.getLogger(__name__)


def load_psa_scenarios(file_path: str) -> list[dict[str, Any]]:
    """Load the PSA scenario definitions from a specified JSON file."""
    try:
        with Path(file_path).open() as f:
            scenarios = json.load(f)
        return cast("list[dict[str, Any]]", scenarios)
    except FileNotFoundError as error:
        message = f"PSA scenarios file not found at: {file_path}"
        raise FileNotFoundError(message) from error
    except json.JSONDecodeError as error:
        message = f"Invalid JSON format in PSA scenarios file: {file_path}"
        raise ValueError(message) from error


@with_config(ConfigDict(strict=True, extra="forbid"))
class SeedOptions(TypedDict):
    """The optional named seed retains the legacy default."""

    seed: NotRequired[int]


SEED_OPTIONS = TypeAdapter(SeedOptions)


def run_psa_analysis(
    base_case_df: pl.DataFrame,
    formulas_data: dict[str, Any],
    calculation_pipeline: Callable[[pl.DataFrame, dict[str, Any]], pl.DataFrame],
    scenarios: list[dict[str, Any]],
    iterations: int,
    **options: Unpack[SeedOptions],
) -> pl.DataFrame:
    """Run a Probabilistic Sensitivity Analysis using Monte Carlo simulation."""
    logger.info("--- Running %s PSA Iterations ---", iterations)
    settings = SEED_OPTIONS.validate_python(options)
    rng = np.random.default_rng(settings.get("seed", 20261103))
    all_results: list[dict[str, int | float]] = []

    param_to_col_map = parameter_mapping(formulas_data)
    # A caller may pass the calculated base case, as the original CLI did.
    # Derived costs must be recalculated after sampling, rather than cached.
    derived = [
        output["name"] + "_Y0"
        for output in formulas_data.get("outputs", [])
        if "name" in output
    ]
    base_inputs = base_case_df.drop(derived, strict=False)

    for i in range(iterations):
        if (i + 1) % 100 == 0:
            logger.info("Running iteration %s/%s...", i + 1, iterations)

        iter_df = base_inputs.clone()

        for scenario in scenarios:
            param = scenario["parameter_to_vary"]
            dist = scenario["distribution"]
            column_to_vary = param_to_col_map.get(param)

            if not column_to_vary:
                logger.warning("Param '%s' not in formula mapping. Skipping.", param)
                continue

            if dist["type"] == "normal":
                sampled_value = rng.normal(dist["mean"], dist["std_dev"])
            elif dist["type"] == "uniform":
                sampled_value = rng.uniform(dist["min"], dist["max"])
            elif dist["type"] == "triangular":
                sampled_value = rng.triangular(dist["min"], dist["mode"], dist["max"])
            else:
                logger.warning("Unknown distribution '%s'. Skipping.", dist["type"])
                continue

            iter_df = iter_df.with_columns(pl.lit(sampled_value).alias(column_to_vary))

        result_df = calculation_pipeline(iter_df, formulas_data)
        mean_cost = numeric(result_df["Calculated_Cost_Mid_Y0"].mean())
        all_results.append({"iteration": i + 1, "mean_cost": mean_cost})

    return pl.DataFrame(all_results)


def report_psa_results(psa_results_df: pl.DataFrame) -> None:
    """Print a summary report of the PSA results."""
    logger.info("--- PSA Results Summary ---")
    if psa_results_df.is_empty():
        logger.info("No PSA results to report.")
        return

    mean_cost = numeric(psa_results_df["mean_cost"].mean())
    std_dev = numeric(psa_results_df["mean_cost"].std())
    confidence_interval = (
        numeric(psa_results_df["mean_cost"].quantile(0.025, interpolation="linear")),
        numeric(psa_results_df["mean_cost"].quantile(0.975, interpolation="linear")),
    )

    logger.info("Number of Iterations: %s", len(psa_results_df))
    logger.info("Average Mean Cost: %s", format(mean_cost, ",.2f"))
    logger.info("Standard Deviation: %s", format(std_dev, ",.2f"))
    logger.info(
        "95%% simulation percentile interval: (%s - %s)",
        format(confidence_interval[0], ",.2f"),
        format(confidence_interval[1], ",.2f"),
    )
