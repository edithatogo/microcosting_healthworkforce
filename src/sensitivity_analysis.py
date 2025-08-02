# src/sensitivity_analysis.py
"""
This module handles the Deterministic Sensitivity Analysis (DSA).

It provides functionality to run pre-defined or custom scenarios,
systematically varying input parameters to assess their impact on the final
calculated costs.
"""

import json
from typing import Any, Dict, List, cast


def load_dsa_scenarios(file_path: str) -> List[Dict[str, Any]]:
    """
    Loads the DSA scenario definitions from a specified JSON file.
    """
    try:
        with open(file_path, "r") as f:
            scenarios = json.load(f)
        return cast(List[Dict[str, Any]], scenarios)
    except FileNotFoundError:
        raise FileNotFoundError(f"DSA scenarios file not found at: {file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in DSA scenarios file: {file_path}")
