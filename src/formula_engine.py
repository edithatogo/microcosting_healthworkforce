# src/formula_engine.py
"""
This module provides the core functionality for the data-driven calculation engine.
It is responsible for loading formula definitions from a JSON file and orchestrating
the calculation process based on those definitions.
"""

import ast
import json
from typing import Any, Dict, cast

import pandas as pd

from src.formula_parser import evaluate_expression


def load_formulas(file_path: str) -> Dict[str, Any]:
    """
    Loads and validates the formula definitions from a specified JSON file.

    Args:
        file_path: The absolute path to the JSON file containing the formulas.

    Returns:
        A dictionary containing the parsed formula definitions.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the JSON file is malformed or missing required keys.
    """
    try:
        with open(file_path, "r") as f:
            formulas_data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Formula file not found at: {file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in file: {file_path}")

    # Basic validation to ensure the core keys are present
    if "formulas" not in formulas_data or "outputs" not in formulas_data:
        raise ValueError(
            f"'{file_path}' is missing required keys: 'formulas' and/or 'outputs'."
        )

    return cast(Dict[str, Any], formulas_data)


def _check_for_override(row: pd.Series, output_def: Dict[str, Any]) -> Any:
    """
    Checks if a hardcoded override value should be used for a given row and output.

    Args:
        row: A Series representing a row of the input DataFrame.
        output_def: The definition of the output being calculated.

    Returns:
        The override value if the conditions are met, otherwise None.
    """
    override_col = output_def.get("override_column")
    override_cond = output_def.get("override_condition")
    if override_col and override_cond and pd.notna(row.get(override_col)):
        try:
            if ast.literal_eval(override_cond):
                return row[override_col]
        except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):  # nosec B110
            pass
    return None


def _calculate_value(
    row: pd.Series,
    output_def: Dict[str, Any],
    formula: Dict[str, Any],
) -> Any:
    """
    Calculates a value using the defined formula expression.

    Args:
        row: A Series representing a row of the input DataFrame.
        output_def: The definition of the output being calculated.
        formula: The formula definition to use for the calculation.

    Returns:
        The calculated value.
    """
    expression = formula["expression"]
    parameters = {
        param_name: row.get(source_col, 0)
        for param_name, source_col in output_def["parameter_mapping"].items()
    }
    for p in formula["parameters"]:
        parameters.setdefault(p, 0)

    if parameters.get("productive_time_factor") == 0:
        parameters["productive_time_factor"] = 1.0

    return evaluate_expression(expression, parameters)


def apply_formulas(
    data_df: pd.DataFrame, formulas_data: Dict[str, Any]
) -> pd.DataFrame:
    """
    Applies the defined formulas to the input DataFrame row by row.
    """
    results = []
    formulas_map = {f["id"]: f for f in formulas_data["formulas"]}

    for _, row in data_df.iterrows():
        row_results = {}
        for output_def in formulas_data["outputs"]:
            output_name = output_def["name"]
            formula_id = output_def["uses_formula"]
            formula = formulas_map[formula_id]

            override_value = _check_for_override(row, output_def)
            if override_value is not None:
                calculated_value = override_value
            else:
                calculated_value = _calculate_value(row, output_def, formula)

            row_results[output_name] = calculated_value
        results.append(row_results)

    return pd.DataFrame(results, index=data_df.index)
