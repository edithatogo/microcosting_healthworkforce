# src/formula_engine.py
"""
This module provides the core functionality for the data-driven calculation engine.
It is responsible for loading formula definitions from a JSON file and orchestrating
the calculation process based on those definitions.
"""

import json
from typing import Any, cast

import pandas as pd

from src.formula_parser import evaluate_expression


def load_formulas(file_path: str) -> dict[str, Any]:
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
        with open(file_path, "r") as f:  # noqa: UP015 - explicit mode for test clarity
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

    return cast(dict[str, Any], formulas_data)


def _calculate_value(
    row: "pd.Series[Any]",
    formula: dict[str, Any],
    intermediate_results: dict[str, Any],
    parameter_mapping: dict[str, str],
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
        import logging

        logging.warning(
            "Productive time factor is 0, setting to 1.0 to avoid division by zero."
        )
        parameters["productive_time_factor"] = 1.0

    return evaluate_expression(expression, parameters)


def apply_formulas(
    data_df: pd.DataFrame, formulas_data: dict[str, Any]
) -> pd.DataFrame:
    """
    Applies the defined formulas to the input DataFrame row by row.
    """
    results = []
    formulas = {f["id"]: f for f in formulas_data.get("formulas", [])}
    outputs = formulas_data.get("outputs", [])

    for _, row in data_df.iterrows():
        row_results = {}
        intermediate_results: dict[str, Any] = {}

        for output_def in outputs:
            output_name = output_def["name"] + "_Y0"
            calculation_method = output_def.get("calculation_method")
            final_value = 0

            if calculation_method == "direct":
                source_col = output_def.get("source_column")
                if source_col:
                    final_value = row.get(source_col, 0)

            elif calculation_method == "formula":
                formula_id = output_def["uses_formula"]
                formula_def = formulas[formula_id]
                param_mapping = output_def.get("parameter_mapping", {})

                # Calculate all dependencies, storing them in intermediate_results
                for dep_id in formula_def.get("dependencies", []):
                    if dep_id not in intermediate_results:
                        dep_formula = formulas[dep_id]
                        intermediate_results[dep_id] = _calculate_value(
                            row, dep_formula, intermediate_results, param_mapping
                        )

                # Now calculate the final formula
                final_value = _calculate_value(
                    row, formula_def, intermediate_results, param_mapping
                )

            row_results[output_name] = final_value
        results.append(row_results)

    results_df = pd.DataFrame(results, index=data_df.index)
    # Drop columns from results_df that are already in data_df to avoid duplication
    results_df = results_df.drop(
        columns=[col for col in results_df.columns if col in data_df.columns]
    )
    return pd.concat([data_df, results_df], axis=1)
