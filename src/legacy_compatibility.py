# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Opt in to the unchanged legacy pipeline with explicit run provenance.

This adapter retains legacy fallback semantics. It does not admit candidate
conditions to a v2 release or independently verify the asserted workbook source.
"""

import hashlib
import json
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import polars as pl
from pydantic import BaseModel, ConfigDict, Field

from src import config
from src.contracts import FORMULA_ADAPTER
from src.formula_engine import apply_formulas
from src.projection import project_costs
from src.rate_converter import convert_annual_cost_to_rates


class CompatibilityRequest(BaseModel):
    """Select the legacy method and retain caller-asserted extraction identity."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    mode: Literal["legacy_compatibility_v1"]
    workbook_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    sheet: str = Field(pattern=r"\S")
    extraction_id: str = Field(pattern=r"\S")
    projection_years: int = Field(default=config.PROJECTION_YEARS, ge=0)


class CompatibilityManifest(CompatibilityRequest):
    """Pin the calculation content without asserting entitlement or source review."""

    input_sha256: str
    formulas_sha256: str
    output_sha256: str
    engine_sha256: str
    python_version: str
    polars_version: str
    source_identity_verified: Literal[False]
    accepted_condition_release: Literal[False]
    run_sha256: str


@dataclass(frozen=True)
class CompatibilityResult:
    """Return the legacy table and its at-calculation fingerprint separately."""

    frame: pl.DataFrame
    manifest: CompatibilityManifest


def _digest(value: object) -> str:
    """Hash deterministic JSON; do not silently serialize arbitrary objects."""
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _frame_digest(frame: pl.DataFrame) -> str:
    """Hash typed scalar content without unused Arrow buffer bytes.

    Polars string conversion preserves null separately from the literal NaN
    representation. The schema binds the original type, column and row order.
    Unsupported string conversions fail instead of hashing an opaque object.
    """
    return _digest(
        {
            "schema": [(name, str(dtype)) for name, dtype in frame.schema.items()],
            "values": frame.select(pl.all().cast(pl.String)).write_json(),
        },
    )


def cost_legacy_compatibility(
    request: CompatibilityRequest,
    inputs: pl.DataFrame,
    formulas: object,
) -> CompatibilityResult:
    """Run the selected legacy calculation without recalculation, writes or PSA.

    Callers supply an already-extracted frame. Workbook provenance is asserted;
    its hash is not a claim that this function opened or checked source bytes.
    The returned table is mutable Polars data; pins describe its original state.
    """
    selected = CompatibilityRequest.model_validate(request.model_dump())
    document = FORMULA_ADAPTER.validate_python(formulas)
    frame = inputs.clone()
    result = convert_annual_cost_to_rates(
        project_costs(
            apply_formulas(frame, document),
            frame,
            selected.projection_years,
        ),
        frame,
    )
    root = Path(__file__).parent
    engine = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in (
            "legacy_compatibility.py",
            "formula_engine.py",
            "contracts.py",
            "projection.py",
            "rate_converter.py",
            "polars_rates.py",
        )
    }
    details: dict[str, object] = {
        **selected.model_dump(),
        "input_sha256": _frame_digest(frame),
        "formulas_sha256": _digest(document),
        "output_sha256": _frame_digest(result),
        "engine_sha256": _digest(engine),
        "python_version": platform.python_version(),
        "polars_version": pl.__version__,
        "source_identity_verified": False,
        "accepted_condition_release": False,
    }
    manifest = CompatibilityManifest.model_validate(
        {
            **details,
            "run_sha256": _digest(details),
        },
    )
    return CompatibilityResult(result, manifest)
