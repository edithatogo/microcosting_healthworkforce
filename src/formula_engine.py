# src/formula_engine.py
"""
This module provides the core functionality for the data-driven calculation engine.
It is responsible for loading formula definitions from a JSON file and orchestrating
the calculation process based on those definitions.
"""

import json
from typing import Any, Dict, cast

import pandas as pd


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
    Applies the defined formulas to the input DataFrame.
    (This is a placeholder for the full implementation).

    Args:
        data_df: The input DataFrame containing the source data.
        formulas_data: The dictionary of formula definitions.

    Returns:
        A DataFrame with the calculated output columns.
    """
    # Placeholder: In the next step, this will iterate through the 'outputs'
    # and apply the 'expression' from the 'formulas' section.
    print("Formula engine (placeholder): Applying formulas...")
    return data_df
