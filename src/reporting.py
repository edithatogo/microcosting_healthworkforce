# src/reporting.py
"""
This module handles the generation of all file-based outputs, including tables
and figures for the core simulation, DSA, and PSA results.
"""

import logging
import os

import pandas as pd


def save_base_case_results(base_case_results: pd.DataFrame, output_dir: str) -> None:
    """
    Saves the base case results to a CSV file.
    """
    output_path = os.path.join(output_dir, "base_case_results.csv")
    try:
        base_case_results.to_csv(output_path, index=False)
        logging.info(f"Base case results saved to {output_path}")
    except Exception as e:
        logging.error(f"Failed to save base case results: {e}")
