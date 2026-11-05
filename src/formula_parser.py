# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Evaluate scalar arithmetic through the shared restricted Polars compiler."""

import ast
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

import polars as pl

from src.formula_engine import compile_expression


def evaluate_expression(expression: str, parameters: Mapping[str, object]) -> object:
    """Evaluate supported arithmetic without a separate interpreter backend."""
    values: dict[str, pl.Expr] = {}
    for name, value in parameters.items():
        if not isinstance(value, (int, float)):
            message = f"Parameter {name} must be numeric"
            raise TypeError(message)
        values[name] = pl.lit(value)
    try:
        compiled = compile_expression(ast.parse(expression, mode="eval").body, values)
        result = _finite_result(pl.select(compiled).item())
    except (SyntaxError, ValueError, pl.exceptions.PolarsError) as error:
        message = f"Error in expression '{expression}': {error}"
        raise ValueError(message) from error
    else:
        return result


def _finite_result(result: object) -> object:
    """Reject invalid arithmetic while retaining the public error context."""
    if isinstance(result, float) and not math.isfinite(result):
        message = "Arithmetic produced a nonfinite result"
        raise ValueError(message)
    return result
