# src/formula_engine.py
"""
This module provides the core functionality for the data-driven calculation engine.
It is responsible for loading formula definitions from a JSON file and orchestrating
the calculation process based on those definitions.
"""

import ast
import json
from typing import Any, Dict, List, cast

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
    formula: Dict[str, Any],
    intermediate_results: Dict[str, Any],
    parameter_mapping: Dict[str, str],
) -> Any:
    """
    Calculates a value using the defined formula expression.

    Args:
        row: A Series representing a row of the input DataFrame.
        formula: The formula definition to use for the calculation.
        intermediate_results: A dictionary of already calculated intermediate values.
        parameter_mapping: A dictionary mapping formula parameters to DataFrame columns.

    Returns:
        The calculated value.
    """
    expression = formula["expression"]
    parameters = {}

    for param_name in formula.get("parameters", []):
        if param_name in intermediate_results:
            parameters[param_name] = intermediate_results[param_name]
        elif param_name in parameter_mapping:
            source_col = parameter_mapping[param_name]
            parameters[param_name] = row.get(source_col, 0)
        else:
            parameters[param_name] = 0

    if parameters.get("productive_time_factor") == 0:
        parameters["productive_time_factor"] = 1.0

    return evaluate_expression(expression, parameters)


def _topological_sort(formulas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sorts formulas based on their dependencies.

    Args:
        formulas: A list of formula definitions.

    Returns:
        A sorted list of formula definitions.
    """
    formulas_map = {f["id"]: f for f in formulas}
    dependencies = {
        f["id"]: f.get("dependencies", [])
        for f in formulas
        if f.get("type") == "dependent"
    }
    sorted_order = []
    visited = set()

    def visit(formula_id: str) -> None:
        if formula_id in visited:
            return
        visited.add(formula_id)
        for dep_id in dependencies.get(formula_id, []):
            visit(dep_id)
        sorted_order.append(formulas_map[formula_id])

    for formula in formulas:
        if formula["id"] not in visited:
            visit(formula["id"])

    return sorted_order


def apply_formulas(
    data_df: pd.DataFrame, formulas_data: Dict[str, Any]
) -> pd.DataFrame:
    """
    Applies the defined formulas to the input DataFrame row by row.
    """
    results = []
    sorted_formulas = _topological_sort(formulas_data["formulas"])

    for _, row in data_df.iterrows():
        row_results = {}
        intermediate_results: Dict[str, Any] = {}

        # Pre-calculate all possible formulas for the row
        for formula in sorted_formulas:
            formula_id = formula["id"]
            # Note: This assumes that the parameter mapping is the same for all formulas
            # that might be used in a row. This is true for our current case.
            parameter_mapping = formulas_data["outputs"][0].get("parameter_mapping", {})
            calculated_value = _calculate_value(
                row, formula, intermediate_results, parameter_mapping
            )
            intermediate_results[formula_id] = calculated_value

        for output_def in formulas_data["outputs"]:
            output_name = output_def["name"] + "_Y0"
            calc_type = output_def.get("calculation_type", "formula")

            final_value = 0
            if calc_type == "direct_input":
                source_col = output_def.get("source_column")
                if source_col:
                    final_value = row.get(source_col, 0)
            elif calc_type == "weekly_rate":
                source_col = output_def.get("source_column")
                if source_col:
                    weekly_rate = row.get(source_col, 0)
                    final_value = weekly_rate * 52
            else:  # Default to "formula"
                final_formula_id = output_def["uses_formula"]
                final_value = intermediate_results[final_formula_id]

            # Override logic remains the same
            override_value = _check_for_override(row, output_def)
            if override_value is not None:
                final_value = override_value

            row_results[output_name] = final_value
        results.append(row_results)

    results_df = pd.DataFrame(results, index=data_df.index)
    return pd.concat([data_df, results_df], axis=1)
