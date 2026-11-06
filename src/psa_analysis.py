# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
# src/psa_analysis.py
"""Simulate workforce costs using declared parameter distributions."""

import json
import logging
from pathlib import Path
from typing import Any, NotRequired, TypedDict, Unpack, cast
lazy from collections.abc import Callable

import polars as pl
from pydantic import ConfigDict, TypeAdapter, with_config

from src.contracts import parameter_mapping
from src.numeric import numeric
from src.psa_simulation import SimulationSpec, complete_mean_cost, parameter_draws

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
    spec = SimulationSpec(iterations=iterations, seed=settings.get("seed", 20261103))
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

    draws = parameter_draws(scenarios, param_to_col_map, set(base_inputs.columns), spec)
    for i, sampled in enumerate(draws):
        if (i + 1) % 100 == 0:
            logger.info("Running iteration %s/%s...", i + 1, iterations)
        iter_df = base_inputs.with_columns(
            pl.lit(value).alias(column) for column, value in sampled.items()
        )

        result_df = calculation_pipeline(iter_df, formulas_data)
        mean_cost = complete_mean_cost(result_df, base_inputs.height)
        all_results.append({"iteration": i + 1, "mean_cost": mean_cost})

    return pl.DataFrame(all_results)


def report_psa_results(psa_results_df: pl.DataFrame) -> None:
    """Print a summary report of the PSA results."""
    logger.info("--- PSA Results Summary ---")
    if psa_results_df.is_empty():
        logger.info("No PSA results to report.")
        return

    logger.warning(
        "Exploratory PSA: results are conditional on supplied assumptions and are "
        "not scientifically validated by this calculation.",
    )
    mean_cost = numeric(psa_results_df["mean_cost"].mean())
    logger.info("Number of Iterations: %s", len(psa_results_df))
    logger.info("Average Mean Cost: %s", format(mean_cost, ",.2f"))
    if psa_results_df.height == 1:
        logger.info("Standard Deviation: undefined for one iteration")
        logger.info("Simulation percentile interval: not estimated for one iteration")
        return
    std_dev = numeric(psa_results_df["mean_cost"].std())
    percentile_interval = (
        numeric(psa_results_df["mean_cost"].quantile(0.025, interpolation="linear")),
        numeric(psa_results_df["mean_cost"].quantile(0.975, interpolation="linear")),
    )

    logger.info("Standard Deviation: %s", format(std_dev, ",.2f"))
    logger.info(
        "95%% simulation percentile interval: (%s - %s)",
        format(percentile_interval[0], ",.2f"),
        format(percentile_interval[1], ",.2f"),
    )
