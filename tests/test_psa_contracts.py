# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Require both PSA entry points to execute the entire declared finite model."""

import argparse
import json
from typing import Any, cast
from unittest.mock import patch
lazy from pathlib import Path

import polars as pl
import pytest

from src.contracts import parameter_mapping
from src.formula_engine import apply_formulas
from src.psa_analysis import run_psa_analysis
from src.workbook_run import WorkforceRun
from tests.checks import assert_that
lazy from src.contracts import FormulaDocument


@pytest.fixture
def simulation() -> dict[str, Any]:
    """Provide a two-role calculation with an observable sampled effect."""
    return {
        "frame": pl.DataFrame({"salary": [100.0, 200.0], "rate": [0.0, 0.0]}),
        "formulas": {
            "formulas": [
                {
                    "id": "cost",
                    "expression": "salary * (1 + rate)",
                    "parameters": ["salary", "rate"],
                },
            ],
            "outputs": [
                {
                    "name": "Calculated_Cost_Mid",
                    "calculation_method": "formula",
                    "uses_formula": "cost",
                    "parameter_mapping": {"salary": "salary", "rate": "rate"},
                },
            ],
        },
        "scenarios": [
            {
                "parameter_to_vary": "rate",
                "distribution": {"type": "normal", "mean": 1.0, "std_dev": 0.0},
            },
        ],
        "iterations": 1,
        "seed": 20261103,
    }


def execute(entrypoint: str, inputs: dict[str, Any], folder: Path) -> pl.DataFrame:
    """Exercise the real API or runner, including its persisted result."""
    if entrypoint == "api":
        return run_psa_analysis(
            inputs["frame"],
            inputs["formulas"],
            apply_formulas,
            inputs["scenarios"],
            inputs["iterations"],
            seed=inputs["seed"],
        )
    args = argparse.Namespace(
        output_dir=str(folder),
        psa_iterations=inputs["iterations"],
        seed=inputs["seed"],
    )
    runner = WorkforceRun(args)
    runner.frame = inputs["frame"]
    runner.formulas = cast("FormulaDocument", inputs["formulas"])
    runner.mapping = parameter_mapping(inputs["formulas"])
    spec_path = folder / "scenarios.json"
    spec_path.write_text(json.dumps(inputs["scenarios"]))
    with patch("src.workbook_run.config.PSA_SCENARIOS_FILE_PATH", str(spec_path)):
        runner.run_psa()
    return pl.read_csv(folder / "psa_results.csv")


@pytest.mark.parametrize("entrypoint", ["api", "runner"])
@pytest.mark.parametrize(
    "scenario",
    [
        {
            "parameter_to_vary": "typo",
            "distribution": {"type": "normal", "mean": 1.0, "std_dev": 0.0},
        },
        {"parameter_to_vary": "rate", "distribution": {"type": "unknown"}},
        {
            "parameter_to_vary": "rate",
            "distribution": {"type": "normal", "mean": float("nan"), "std_dev": 0.0},
        },
        {
            "parameter_to_vary": "rate",
            "distribution": {"type": "uniform", "min": 2.0, "max": 1.0},
        },
        {
            "parameter_to_vary": "rate",
            "distribution": {"type": "triangular", "min": 0.0, "mode": 3.0, "max": 2.0},
        },
    ],
)
def test_invalid_scenario_fails_before_output(
    entrypoint: str,
    scenario: dict[str, Any],
    simulation: dict[str, Any],
    tmp_path: Path,
) -> None:
    """Catch silent omission of requested uncertainty or invalid distribution data."""
    simulation["scenarios"] = [scenario]
    with pytest.raises(ValueError, match=r"unmapped|validation error"):
        execute(entrypoint, simulation, tmp_path)
    assert_that(not (tmp_path / "psa_results.csv").exists())


@pytest.mark.parametrize("entrypoint", ["api", "runner"])
@pytest.mark.parametrize("iterations", [0, -1, True])
def test_nonpositive_or_boolean_iterations_rejected(
    entrypoint: str,
    iterations: int,
    simulation: dict[str, Any],
    tmp_path: Path,
) -> None:
    """Catch empty simulations or bool-to-int coercion of run length."""
    simulation["iterations"] = iterations
    with pytest.raises(ValueError, match="iterations"):
        execute(entrypoint, simulation, tmp_path)


@pytest.mark.parametrize("entrypoint", ["api", "runner"])
def test_duplicate_parameter_rejected(
    entrypoint: str,
    simulation: dict[str, Any],
    tmp_path: Path,
) -> None:
    """Catch a later draw silently overwriting an earlier parameter definition."""
    simulation["scenarios"] *= 2
    with pytest.raises(ValueError, match="unique"):
        execute(entrypoint, simulation, tmp_path)


@pytest.mark.parametrize("entrypoint", ["api", "runner"])
@pytest.mark.parametrize("bad_salary", [None, float("inf")])
def test_incomplete_or_nonfinite_cost_rows_rejected(
    entrypoint: str,
    bad_salary: float | None,
    simulation: dict[str, Any],
    tmp_path: Path,
) -> None:
    """Catch a finite-looking mean that omitted a missing or invalid role cost."""
    simulation["frame"] = pl.DataFrame(
        {"salary": [bad_salary, 200.0], "rate": [0.0, 0.0]},
    )
    with pytest.raises(ValueError, match="finite numeric cost"):
        execute(entrypoint, simulation, tmp_path)
    assert_that(not (tmp_path / "psa_results.csv").exists())


def test_api_and_runner_agree_on_seeded_valid_model(
    simulation: dict[str, Any],
    tmp_path: Path,
) -> None:
    """Catch differing draw order or aggregation between the real entry points."""
    simulation["iterations"] = 3
    simulation["scenarios"][0]["distribution"]["std_dev"] = 0.1
    api = execute("api", simulation, tmp_path)
    runner = execute("runner", simulation, tmp_path)
    assert_that(api.equals(runner))
