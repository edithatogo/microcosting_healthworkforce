# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Shared, non-coercing contracts for workforce formula and scenario inputs."""

from typing import NotRequired, TypedDict

from pydantic import ConfigDict, TypeAdapter, with_config


@with_config(ConfigDict(extra="allow", strict=True))
class FormulaDefinition(TypedDict):
    """Describe arithmetic while retaining optional workbook metadata."""

    id: str
    expression: str
    parameters: NotRequired[list[str]]
    dependencies: NotRequired[list[str]]


@with_config(ConfigDict(extra="allow", strict=True))
class OutputDefinition(TypedDict):
    """Describe a direct or calculated output; execution checks required fields."""

    name: str
    calculation_method: str
    source_column: NotRequired[str]
    uses_formula: NotRequired[str]
    parameter_mapping: NotRequired[dict[str, str]]


@with_config(ConfigDict(extra="allow", strict=True))
class FormulaDocument(TypedDict):
    """Retain definitions and output declarations without coercion."""

    formulas: list[FormulaDefinition]
    outputs: list[OutputDefinition]


@with_config(ConfigDict(extra="allow", strict=True))
class ParameterOutput(TypedDict, total=False):
    """Read just the mapping needed by scenario orchestration."""

    parameter_mapping: dict[str, str]


@with_config(ConfigDict(extra="allow", strict=True))
class ParameterDocument(TypedDict, total=False):
    """Allow scenario-only callers without requiring a complete formula engine."""

    outputs: list[ParameterOutput]


FORMULA_ADAPTER = TypeAdapter(FormulaDocument)
PARAMETER_ADAPTER = TypeAdapter(ParameterDocument)


def parameter_mapping(document: object) -> dict[str, str]:
    """Validate and combine output mappings in their original declaration order."""
    contract = PARAMETER_ADAPTER.validate_python(document)
    result: dict[str, str] = {}
    for output in contract.get("outputs", []):
        result.update(output.get("parameter_mapping", {}))
    return result
