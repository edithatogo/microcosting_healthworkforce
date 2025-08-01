# src/formula_engine.py
"""
This module provides the core functionality for the data-driven calculation engine.
It is responsible for loading formula definitions from a JSON file and orchestrating
the calculation process based on those definitions.
"""

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


def apply_formulas(
    data_df: pd.DataFrame, formulas_data: Dict[str, Any]
) -> pd.DataFrame:
    """
    Applies the defined formulas to the input DataFrame row by row.

    Args:
        data_df: The input DataFrame containing the source data.
        formulas_data: The dictionary of formula definitions.

    Returns:
        A DataFrame with the calculated output columns.
    """
    results = []
    formulas_map = {f["id"]: f for f in formulas_data["formulas"]}

    for _, row in data_df.iterrows():
        row_results = {}
        for output_def in formulas_data["outputs"]:
            output_name = output_def["name"]
            formula_id = output_def["uses_formula"]
            formula = formulas_map[formula_id]
            expression = formula["expression"]

            # Check for hardcoded override value first
            override_col = output_def.get("override_column")
            if override_col and pd.notna(row.get(override_col)):
                calculated_value = row[override_col]
            else:
                # Map parameters from the row to the formula's parameter names
                parameters = {
                    param_name: row.get(source_col, 0)
                    for param_name, source_col in output_def[
                        "parameter_mapping"
                    ].items()
                }
                # Fill any missing parameters with 0
                for p in formula["parameters"]:
                    if p not in parameters:
                        parameters[p] = 0

                # Handle potential division by zero for productive_time_factor
                if (
                    "productive_time_factor" in parameters
                    and parameters["productive_time_factor"] == 0
                ):
                    parameters["productive_time_factor"] = 1.0

                calculated_value = evaluate_expression(expression, parameters)

            row_results[output_name] = calculated_value
        results.append(row_results)

    return pd.DataFrame(results, index=data_df.index)
