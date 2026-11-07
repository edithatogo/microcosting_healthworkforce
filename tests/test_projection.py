# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Explicit workbook indexation on aligned salary-dependent cost bases."""

import polars as pl
import pytest

from src.projection import project_workbook_costs, project_workbook_pda_amount
from tests.checks import assert_that


def test_workbook_projection_uses_simple_indexation_and_fixed_cost() -> None:
    """Preserve each tier and index only the salary-dependent portion."""
    base = pl.DataFrame(
        {
            "Calculated_Cost_LL_Y0": [100000, 100000],
            "Calculated_Cost_Mid_Y0": [110000, 110000],
            "Calculated_Cost_UL_Y0": [120000, 120000],
        },
    )
    result = project_workbook_costs(
        base,
        pl.Series([0.015, 0.0]),
        pl.Series([10000, 10000]),
    )
    assert_that(
        result["Calculated_Cost_Mid_Y1"].to_list()
        == pytest.approx([110015, 110000], abs=1e-8, rel=0),
    )
    assert_that(
        result["Calculated_Cost_LL_Y4"].to_list()
        == pytest.approx([100054, 100000], abs=1e-8, rel=0),
    )
    assert_that(
        result["Calculated_Cost_Mid_Y4"].to_list()
        == pytest.approx([110060, 110000], abs=1e-8, rel=0),
    )
    assert_that(
        result["Calculated_Cost_UL_Y4"].to_list()
        == pytest.approx([120066, 120000], abs=1e-8, rel=0),
    )
    with pytest.raises(ValueError, match="align"):
        project_workbook_costs(base, pl.Series([0.015]), pl.Series([10000, 10000]))
    with pytest.raises(ValueError, match="finite"):
        project_workbook_costs(
            base,
            pl.Series([0.015, None]),
            pl.Series([10000, 10000]),
        )


def test_pda_projection_preserves_binary_rounding_boundary() -> None:
    """Replay the cached binary rounding on either side of a boundary."""
    assert_that(project_workbook_pda_amount(1.15, 1) == pytest.approx(1.1))
    assert_that(project_workbook_pda_amount(1.16, 1) == pytest.approx(1.2))
    with pytest.raises(ValueError, match="finite"):
        project_workbook_pda_amount(100, float("nan"))
