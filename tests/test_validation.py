# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
# tests/test_validation.py
"""Test for the validation module."""

import polars as pl
import pytest

from src.validation import validate_dsa_results, validate_psa_results
from tests.checks import assert_that


def test_validate_dsa_results_success() -> None:
    """Accept DSA results that agree with their reference."""
    dsa_results = {"Scenario A": pl.DataFrame({"Calculated_Cost_Mid_Y0": [100]})}
    validation_df = pl.DataFrame({"Scenario A_Base Salary + Costs_MP": [100]})
    scenario_map = {"Scenario A": "Scenario A_Base Salary + Costs_MP"}
    assert_that(validate_dsa_results(dsa_results, validation_df, scenario_map))


def test_validate_dsa_results_failure() -> None:
    """Reject DSA results that disagree with their reference."""
    dsa_results = {"Scenario A": pl.DataFrame({"Calculated_Cost_Mid_Y0": [110]})}
    validation_df = pl.DataFrame({"Scenario A_Base Salary + Costs_MP": [100]})
    scenario_map = {"Scenario A": "Scenario A_Base Salary + Costs_MP"}
    assert_that(not validate_dsa_results(dsa_results, validation_df, scenario_map))


@pytest.mark.parametrize("value", [None, float("nan"), float("inf"), float("-inf")])
def test_dsa_validation_rejects_nonfinite_evidence(value: float | None) -> None:
    """Missing and nonfinite values on both sides are not matching evidence."""
    result = pl.DataFrame(
        {"Calculated_Cost_Mid_Y0": [value]},
        schema={"Calculated_Cost_Mid_Y0": pl.Float64},
    )
    reference = pl.DataFrame({"expected": [value]}, schema={"expected": pl.Float64})
    assert_that(
        not validate_dsa_results({"case": result}, reference, {"case": "expected"}),
    )


def test_dsa_validation_rejects_empty_comparisons() -> None:
    """Two empty columns do not constitute a successful comparison."""
    result = pl.DataFrame(schema={"Calculated_Cost_Mid_Y0": pl.Float64})
    reference = pl.DataFrame(schema={"expected": pl.Float64})
    assert_that(
        not validate_dsa_results({"case": result}, reference, {"case": "expected"}),
    )


def test_validate_psa_results_success() -> None:
    """Accept PSA results that agree with their reference."""
    psa_results = pl.DataFrame({"mean_cost": [100, 110, 120]})
    validation_df = pl.DataFrame({"Expected Mean Cost": [110]})
    assert_that(validate_psa_results(psa_results, validation_df))


def test_validate_psa_results_failure() -> None:
    """Reject PSA results that disagree with their reference."""
    psa_results = pl.DataFrame({"mean_cost": [100, 110, 120]})
    validation_df = pl.DataFrame({"Expected Mean Cost": [150]})
    assert_that(not validate_psa_results(psa_results, validation_df))


def test_validate_psa_results_empty_results() -> None:
    """Reject an absent simulation instead of claiming successful validation."""
    psa_results = pl.DataFrame({"mean_cost": []})
    validation_df = pl.DataFrame({"Expected Mean Cost": [150]})
    assert_that(not validate_psa_results(psa_results, validation_df))


def test_validate_psa_results_missing_validation_column() -> None:
    """Report a missing reference column without claiming validation."""
    psa_results = pl.DataFrame({"mean_cost": [100, 110, 120]})
    validation_df = pl.DataFrame({"Some Other Column": [150]})
    assert_that(not validate_psa_results(psa_results, validation_df))


@pytest.mark.parametrize(
    "values",
    [[None, 110.0], [float("nan"), 110.0], [float("inf"), 110.0], ["110", "110"]],
)
def test_psa_validation_rejects_invalid_draws(values: list[object]) -> None:
    """Catch missing, nonfinite or nonnumeric draws hidden by a mean summary."""
    assert_that(
        not validate_psa_results(
            pl.DataFrame({"mean_cost": values}),
            pl.DataFrame({"Expected Mean Cost": [110.0]}),
        ),
    )


@pytest.mark.parametrize(
    "values",
    [[], [None], [float("nan")], [float("inf")], [110.0, 110.0], ["110"]],
)
def test_psa_validation_rejects_invalid_reference(
    values: list[object],
) -> None:
    """Catch missing, ambiguous or invalid reference values before comparison."""
    assert_that(
        not validate_psa_results(
            pl.DataFrame({"mean_cost": [110.0]}),
            pl.DataFrame({"Expected Mean Cost": values}),
        ),
    )


def test_psa_validation_requires_cost_column() -> None:
    """Reject a result table without costs instead of raising during reduction."""
    assert_that(
        not validate_psa_results(
            pl.DataFrame({"iteration": [1]}),
            pl.DataFrame({"Expected Mean Cost": [110.0]}),
        ),
    )


@pytest.mark.parametrize("tolerance", [-1.0, float("nan"), float("inf")])
def test_psa_validation_rejects_invalid_tolerance(tolerance: float) -> None:
    """Catch a tolerance that could bypass a meaningful relative comparison."""
    assert_that(
        not validate_psa_results(
            pl.DataFrame({"mean_cost": [110.0]}),
            pl.DataFrame({"Expected Mean Cost": [110.0]}),
            tolerance,
        ),
    )


def test_psa_comparison_exposes_absolute_tolerance() -> None:
    """Catch an implicit near-zero tolerance defeating a requested exact comparison."""
    results = pl.DataFrame({"mean_cost": [1e-9]})
    reference = pl.DataFrame({"Expected Mean Cost": [0.0]})
    assert_that(validate_psa_results(results, reference, tolerance=0.0))
    assert_that(
        not validate_psa_results(
            results,
            reference,
            tolerance=0.0,
            absolute_tolerance=0.0,
        ),
    )


@pytest.mark.parametrize("absolute_tolerance", [-1.0, float("nan"), float("inf")])
def test_psa_comparison_rejects_invalid_atol(
    absolute_tolerance: float,
) -> None:
    """Reject an invalid absolute tolerance before comparing evidence."""
    assert_that(
        not validate_psa_results(
            pl.DataFrame({"mean_cost": [0.0]}),
            pl.DataFrame({"Expected Mean Cost": [0.0]}),
            absolute_tolerance=absolute_tolerance,
        ),
    )
