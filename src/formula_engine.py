# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
# src/formula_engine.py
"""Compile configured arithmetic into Polars expressions."""

import ast
import json
import logging
import operator
from pathlib import Path
from typing import TYPE_CHECKING

import polars as pl

from src.contracts import FORMULA_ADAPTER, FormulaDocument, OutputDefinition

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


def load_formulas(file_path: str) -> FormulaDocument:
    """Load and validates the formula definitions from a specified JSON file.

    Args:
        file_path: The absolute path to the JSON file containing the formulas.

    Returns:
        A dictionary containing the parsed formula definitions.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the JSON file is malformed or missing required keys.

    """
    try:
        with Path(file_path).open() as f:
            formulas_data = json.load(f)
    except FileNotFoundError as error:
        message = f"Formula file not found at: {file_path}"
        raise FileNotFoundError(message) from error
    except json.JSONDecodeError as error:
        message = f"Invalid JSON format in file: {file_path}"
        raise ValueError(message) from error

    # Basic validation to ensure the core keys are present
    if "formulas" not in formulas_data or "outputs" not in formulas_data:
        message = (
            f"'{file_path}' is missing required keys: 'formulas' and/or 'outputs'."
        )
        raise ValueError(
            message,
        )

    return FORMULA_ADAPTER.validate_python(formulas_data)


def compile_expression(node: ast.AST, parameters: dict[str, pl.Expr]) -> pl.Expr:
    """Compile the supported arithmetic AST using explicit parameter bindings."""
    operations: dict[type[ast.operator], Callable[[pl.Expr, pl.Expr], pl.Expr]] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: lambda a, b: a / b,
        ast.Pow: lambda a, b: a**b,
    }
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return pl.lit(node.value)
    if isinstance(node, ast.Name) and node.id in parameters:
        return parameters[node.id]
    if isinstance(node, ast.BinOp) and type(node.op) in operations:
        return operations[type(node.op)](
            compile_expression(node.left, parameters),
            compile_expression(node.right, parameters),
        )
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = compile_expression(node.operand, parameters)
        return -value if isinstance(node.op, ast.USub) else value
    message = "Unsupported workforce formula expression"
    raise ValueError(message)


def _productive_factor(
    data: pl.DataFrame,
    column: str | None,
    value: pl.Expr,
) -> pl.Expr:
    """Retain the legacy missing/zero-factor warning and neutral multiplier."""
    if column is None or column not in data.columns or (data[column] == 0).any():
        logger.warning("Productive time factor is 0 or missing; using 1.0")
    return pl.when(value == 0).then(1.0).otherwise(value)


def _direct_column(data: pl.DataFrame, name: str) -> pl.Expr:
    """Preserve the source dtype for direct outputs and zero for missing columns."""
    return pl.col(name) if name in data.columns else pl.lit(0.0)


def apply_formulas(
    data_df: pl.DataFrame,
    formulas_data: object,
) -> pl.DataFrame:
    """Resolve each output's own mappings before compiling its expression tree."""
    document = FORMULA_ADAPTER.validate_python(formulas_data)
    formulas = {f["id"]: f for f in document["formulas"]}
    outputs: list[pl.Expr] = []

    def column(name: str | None) -> pl.Expr:
        if name is not None and name in data_df.columns:
            return pl.col(name).cast(pl.Float64)
        return pl.lit(0.0)

    def resolve(key: str, mapping: dict[str, str], visiting: set[str]) -> pl.Expr:
        if key in visiting:
            message = "Cyclic formula dependency"
            raise ValueError(message)
        definition = formulas[key]
        if "parameters" not in definition:
            message = f"Formula {key} has no parameter declaration"
            raise ValueError(message)
        deps = definition.get("dependencies", [])
        args = {
            p: resolve(p, mapping, visiting | {key})
            if p in deps
            else column(mapping.get(p))
            for p in definition["parameters"]
        }
        if "productive_time_factor" in args:
            args["productive_time_factor"] = _productive_factor(
                data_df,
                mapping.get("productive_time_factor"),
                args["productive_time_factor"],
            )
        return compile_expression(
            ast.parse(definition["expression"], mode="eval").body,
            args,
        )

    for output in document["outputs"]:
        name = str(output["name"]) + "_Y0"
        if name in data_df.columns:
            continue
        expr = _output_expression(data_df, output, resolve)
        outputs.append(expr.alias(name))
    return data_df.with_columns(outputs)


def _output_expression(
    data: pl.DataFrame,
    output: OutputDefinition,
    resolve: Callable[[str, dict[str, str], set[str]], pl.Expr],
) -> pl.Expr:
    """Select the declared output method without altering formula resolution."""
    if output["calculation_method"] == "direct" and "source_column" in output:
        source = output["source_column"]
        return _direct_column(data, source)
    if (
        output["calculation_method"] == "formula"
        and "uses_formula" in output
        and "parameter_mapping" in output
    ):
        return resolve(output["uses_formula"], output["parameter_mapping"], set())
    message = "Unknown calculation method"
    raise ValueError(message)
