# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Shared finite, ordered sampling contracts for workforce PSA entry points."""

import math
from typing import Annotated, Literal, Self
lazy from collections.abc import Iterator

import numpy as np
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    FiniteFloat,
    TypeAdapter,
    model_validator,
)
lazy import polars as pl

from src.numeric import numeric


class StrictPSAModel(BaseModel):
    """Reject coercion and undeclared fields at a simulation boundary."""

    model_config = ConfigDict(strict=True, extra="forbid")


class SimulationSpec(StrictPSAModel):
    """Require an actual positive run length and a nonnegative integer seed."""

    iterations: int = Field(gt=0)
    seed: int = Field(ge=0)


class NormalDistribution(StrictPSAModel):
    """Retain finite normal parameters, including a deterministic zero scale."""

    kind: Literal["normal"] = Field(alias="type")
    mean: FiniteFloat
    std_dev: FiniteFloat = Field(ge=0)


class UniformDistribution(StrictPSAModel):
    """Retain ordered finite uniform endpoints without changing their units."""

    kind: Literal["uniform"] = Field(alias="type")
    lower: FiniteFloat = Field(alias="min")
    upper: FiniteFloat = Field(alias="max")

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Reject reversed endpoints before any parameter is drawn."""
        if self.upper < self.lower:
            message = "Uniform minimum must not exceed maximum"
            raise ValueError(message)
        return self


class TriangularDistribution(StrictPSAModel):
    """Retain ordered finite triangular endpoints and mode."""

    kind: Literal["triangular"] = Field(alias="type")
    lower: FiniteFloat = Field(alias="min")
    mode: FiniteFloat
    upper: FiniteFloat = Field(alias="max")

    @model_validator(mode="after")
    def validate_bounds(self) -> Self:
        """Reject a zero-width triangle or a mode outside its support."""
        if not self.lower <= self.mode <= self.upper or self.lower == self.upper:
            message = "Triangular support must contain its mode and have positive width"
            raise ValueError(message)
        return self


Distribution = Annotated[
    NormalDistribution | UniformDistribution | TriangularDistribution,
    Field(discriminator="kind"),
]


class PSAScenario(StrictPSAModel):
    """Name one independently drawn parameter in the declared source order."""

    parameter_to_vary: str = Field(min_length=1)
    distribution: Distribution


SCENARIO_ADAPTER = TypeAdapter(Annotated[list[PSAScenario], Field(min_length=1)])


def sample_distribution(distribution: Distribution, rng: np.random.Generator) -> float:
    """Use the unchanged NumPy scalar distributions and reject nonfinite draws."""
    if isinstance(distribution, NormalDistribution):
        value = float(rng.normal(distribution.mean, distribution.std_dev))
    elif isinstance(distribution, UniformDistribution):
        value = float(rng.uniform(distribution.lower, distribution.upper))
    else:
        value = float(
            rng.triangular(
                distribution.lower,
                distribution.mode,
                distribution.upper,
            ),
        )
    if not math.isfinite(value):
        message = "PSA produced a nonfinite parameter draw"
        raise ValueError(message)
    return value


def parameter_draws(
    scenarios: object,
    mapping: dict[str, str],
    columns: set[str],
    spec: SimulationSpec,
) -> Iterator[dict[str, float]]:
    """Validate the entire joint specification before yielding ordered draws."""
    declared = SCENARIO_ADAPTER.validate_python(scenarios)
    names = [scenario.parameter_to_vary for scenario in declared]
    if len(set(names)) != len(names):
        message = "PSA parameter definitions must be unique"
        raise ValueError(message)
    if set(names) - mapping.keys():
        message = "PSA contains an unmapped parameter"
        raise ValueError(message)
    targets = [mapping[name] for name in names]
    if len(set(targets)) != len(targets) or set(targets) - columns:
        message = "PSA target columns must exist and be unambiguous"
        raise ValueError(message)
    rng = np.random.default_rng(spec.seed)
    for _ in range(spec.iterations):
        yield {
            column: sample_distribution(scenario.distribution, rng)
            for column, scenario in zip(targets, declared, strict=True)
        }


def complete_mean_cost(result: pl.DataFrame, expected_rows: int) -> float:
    """Reject omitted or nonfinite role costs before taking their unweighted mean."""
    column = "Calculated_Cost_Mid_Y0"
    if expected_rows <= 0 or result.height != expected_rows or column not in result:
        message = "PSA calculation must retain every workforce row and its cost"
        raise ValueError(message)
    costs = result[column]
    if (
        not costs.dtype.is_numeric()
        or costs.null_count()
        or not costs.is_finite().all()
    ):
        message = "PSA requires a complete finite numeric cost for every row"
        raise ValueError(message)
    mean = numeric(costs.mean())
    if not math.isfinite(mean):
        message = "PSA mean cost is nonfinite"
        raise ValueError(message)
    return mean
