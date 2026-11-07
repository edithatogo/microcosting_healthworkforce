# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Explicit legacy mode preserves its pipeline and declares its limitations."""

from io import BytesIO

import polars as pl
import pytest
from polars.testing import assert_frame_equal
from pydantic import ValidationError

from src.data_loader import load_and_clean_data
from src.formula_engine import load_formulas
from src.legacy_compatibility import CompatibilityRequest, cost_legacy_compatibility
from src.workbook_run import WorkforceRun
from tests.checks import assert_that
lazy from src.contracts import FormulaDocument


def request() -> CompatibilityRequest:
    """Supply source identity without claiming a file was independently verified."""
    return CompatibilityRequest(
        mode="legacy_compatibility_v1",
        workbook_sha256="a" * 64,
        sheet="Synthetic inputs",
        extraction_id="synthetic-v1",
    )


def inputs() -> pl.DataFrame:
    """One synthetic salary row with an explicit weekly-hours denominator."""
    return pl.DataFrame(
        {
            "Jurisdiction": ["Synthetic"],
            "Personnel type": ["Synthetic role"],
            "salary": [104000.0],
            "Grade(s)_Hours per week": [40.0],
            "Grade(s)_Indexation per annum (%)": [0.1],
        },
    )


def formulas() -> FormulaDocument:
    """Use all three legacy output tiers without real workbook values."""
    return {
        "formulas": [],
        "outputs": [
            {
                "name": f"Calculated_Cost_{tier}",
                "calculation_method": "direct",
                "source_column": "salary",
            }
            for tier in ("LL", "Mid", "UL")
        ],
    }


def test_compatibility_matches_existing_pipeline_and_independent_amounts() -> None:
    """104000/year is 50/hour; ten percent indexation gives 114400 in year one."""
    frame = inputs()
    result = cost_legacy_compatibility(request(), frame, formulas())
    owner = object.__new__(WorkforceRun)
    owner.formulas = formulas()
    assert_frame_equal(result.frame, owner.calculate(frame))
    expected_hourly = 50.0
    assert_that(result.frame["Calculated_Hourly_Mid_Y0"][0] == expected_hourly)
    assert_that(result.frame["Calculated_Cost_Mid_Y1"][0] == pytest.approx(114400))
    assert_that("Calculated_Cost_Mid_Y5" in result.frame.columns)
    expected_years = 5
    assert_that(result.manifest.projection_years == expected_years)
    assert_that(result.manifest.source_identity_verified is False)
    assert_that(result.manifest.accepted_condition_release is False)
    assert_frame_equal(frame, inputs())


def test_compatibility_preserves_missing_column_and_indexation_defaults() -> None:
    """The opt-in adapter preserves a legacy zero instead of claiming v2 admission."""
    frame = (
        inputs()
        .drop("salary")
        .with_columns(
            pl.lit(None, dtype=pl.Float64).alias("Grade(s)_Indexation per annum (%)"),
        )
    )
    result = cost_legacy_compatibility(request(), frame, formulas())
    assert_that(result.frame["Calculated_Cost_Mid_Y5"][0] == 0.0)
    assert_that(result.manifest.mode == "legacy_compatibility_v1")


def test_compatibility_manifest_changes_with_inputs_source_and_formula() -> None:
    """Run pins bind actual table/configuration content and asserted source identity."""
    first = cost_legacy_compatibility(request(), inputs(), formulas())
    changed = cost_legacy_compatibility(
        request(),
        inputs().with_columns(pl.col("salary") * 2),
        formulas(),
    )
    expected_scaled = 100.0
    assert_that(changed.frame["Calculated_Hourly_Mid_Y0"][0] == expected_scaled)
    assert_that(first.manifest.input_sha256 != changed.manifest.input_sha256)
    assert_that(first.manifest.run_sha256 != changed.manifest.run_sha256)
    source = request().model_copy(update={"workbook_sha256": "b" * 64})
    alternate = cost_legacy_compatibility(source, inputs(), formulas())
    assert_that(first.manifest.run_sha256 != alternate.manifest.run_sha256)
    renamed = formulas()
    renamed["outputs"][0]["source_column"] = "missing"
    other = cost_legacy_compatibility(request(), inputs(), renamed)
    assert_that(first.manifest.formulas_sha256 != other.manifest.formulas_sha256)


def test_compatibility_requires_explicit_mode_and_revalidates_copied_request() -> None:
    """Unselected modes, missing identities and forged horizons cannot pass silently."""
    payload = request().model_dump()
    payload.pop("mode")
    with pytest.raises(ValidationError):
        CompatibilityRequest.model_validate(payload)
    invalid = request().model_copy(update={"projection_years": -1})
    with pytest.raises(ValidationError):
        cost_legacy_compatibility(invalid, inputs(), formulas())


def test_compatibility_distinguishes_nan_null_and_explicit_zero_year_horizon() -> None:
    """Null and NaN must not collapse into an identical input fingerprint."""
    null = inputs().with_columns(pl.lit(None, dtype=pl.Float64).alias("unused"))
    nan = inputs().with_columns(pl.lit(float("nan")).alias("unused"))
    first = cost_legacy_compatibility(request(), null, formulas())
    other = cost_legacy_compatibility(request(), nan, formulas())
    assert_that(first.manifest.input_sha256 != other.manifest.input_sha256)
    selected = request().model_copy(update={"projection_years": 0})
    snapshot = cost_legacy_compatibility(selected, inputs(), formulas())
    assert_that("Calculated_Cost_Mid_Y1" not in snapshot.frame.columns)
    assert_that(snapshot.manifest.projection_years == 0)


def test_compatibility_identity_survives_lossless_table_storage() -> None:
    """Typed table identity must not depend on unused null-buffer storage bytes."""
    frame = inputs().with_columns(
        pl.lit(None, dtype=pl.Float64).alias("missing_number"),
        pl.lit(None, dtype=pl.String).alias("missing_text"),
    )
    storage = BytesIO()
    frame.write_parquet(storage)
    restored = pl.read_parquet(storage.getvalue())
    assert_frame_equal(frame, restored)
    first = cost_legacy_compatibility(request(), frame, formulas())
    replay = cost_legacy_compatibility(request(), restored, formulas())
    assert_that(first.manifest == replay.manifest)


def test_workbook_projection_is_explicit_and_adjusts_fixed_cost() -> None:
    """Replay four simple-indexation years with the adjusted fixed allowance."""
    owner = object.__new__(WorkforceRun)
    owner.formulas = formulas()
    owner.mapping = {
        "professional_development_allowance": "development",
        "productive_time_factor": "productive",
    }
    frame = inputs().with_columns(
        pl.lit(2000.0).alias("development"),
        pl.lit(0.5).alias("productive"),
    )
    workbook = owner.calculate(frame, workbook_projection=True)
    default = owner.calculate(frame)
    assert_that(workbook["Calculated_Cost_Mid_Y4"][0] == pytest.approx(104400))
    assert_that(workbook["Calculated_Hourly_Mid_Y4"][0] == pytest.approx(104400 / 2080))
    assert_that("Calculated_Cost_Mid_Y5" not in workbook.columns)
    assert_that("Calculated_Cost_Mid_Y5" in default.columns)


@pytest.mark.parametrize("rename_inputs", [False, True])
def test_explicit_workbook_projection_replays_nsw_admin_midpoint(
    *,
    rename_inputs: bool,
) -> None:
    """Replay the original year-four formula without changing compound mode."""
    data = load_and_clean_data(
        "data/Labour Model - v3, 20240328.xlsx",
        "Labour - Prices",
    )
    admin = data.filter(
        pl.col("Jurisdiction").cast(pl.String).str.contains("NSW")
        & pl.col("Personnel type").cast(pl.String).str.contains("(?i)admin"),
    )
    formulas = load_formulas("data/formulas.json")
    if rename_inputs:
        midpoint = formulas["outputs"][1]
        if "parameter_mapping" not in midpoint:
            raise AssertionError
        mapping = midpoint["parameter_mapping"]
        for key in ("productive_time_factor", "professional_development_allowance"):
            admin = admin.rename({mapping[key]: key})
            mapping[key] = key
    replay = cost_legacy_compatibility(
        request().model_copy(update={"mode": "workbook_projection_v1"}),
        admin,
        formulas,
    )
    compound = cost_legacy_compatibility(request(), admin, formulas)
    assert_that(replay.manifest.mode == "workbook_projection_v1")
    assert_that(
        replay.frame["Calculated_Cost_Mid_Y4"][0] == pytest.approx(136997.189904528),
    )
    assert_that(
        compound.frame["Calculated_Cost_Mid_Y4"][0] == pytest.approx(145316.633922364),
    )
