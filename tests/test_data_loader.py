# tests/test_data_loader.py
"""
Tests for the data_loader module.
"""

from unittest.mock import patch

import pandas as pd

from src import config
from src.data_loader import (
    load_and_clean_data,
    load_dsa_validation_data,
)


def test_load_and_clean_data() -> None:
    """
    Tests that the load_and_clean_data function loads and cleans data correctly.
    """
    # Create a mock DataFrame to be returned by pd.read_excel
    mock_df = pd.DataFrame(
        {
            ("Jurisdiction_", "nan"): ["NSW", "NSW", "VIC"],
            ("Personnel type_", "nan"): ["Nurse", "Doctor", "Admin"],
            ("Base Salary_LL", "nan"): [50000, 80000, 40000],
        }
    )
    mock_df.columns = pd.MultiIndex.from_tuples(mock_df.columns)

    with patch("pandas.read_excel", return_value=mock_df) as mock_read_excel:
        df = load_and_clean_data("dummy_path.xlsx", "dummy_sheet")
        mock_read_excel.assert_called_once_with(
            "dummy_path.xlsx", sheet_name="dummy_sheet", header=[1, 2]
        )
        assert "Jurisdiction" in df.columns
        assert "Personnel type" in df.columns
        assert df.shape[0] == 3
        assert df["Jurisdiction"].isna().sum() == 0
        assert df["Personnel type"].isna().sum() == 0


def test_load_dsa_validation_data() -> None:
    """
    Tests that the load_dsa_validation_data function loads and cleans data correctly.
    """
    # Create a mock DataFrame to be returned by pd.read_excel
    mock_df = pd.DataFrame(
        {
            ("Jurisdiction", "Personnel type", "LL"): [
                "Nurse",
                "Doctor",
                "Admin",
            ],
            ("Superannuation Rate", "Base Salary + Costs", "MP"): [
                0.1,
                0.12,
                0.09,
            ],
        }
    )
    mock_df.columns = pd.MultiIndex.from_tuples(mock_df.columns)

    with patch("pandas.read_excel", return_value=mock_df) as mock_read_excel:
        df = load_dsa_validation_data("dummy_path.xlsx", config.DSA_VALIDATION_SHEET)
        mock_read_excel.assert_called_once_with(
            "dummy_path.xlsx",
            sheet_name=config.DSA_VALIDATION_SHEET,
            header=[0, 1, 2],
        )
        assert "Personnel type" in df.columns
        assert df.shape[0] == 3
        assert df["Personnel type"].isna().sum() == 0
        assert "Superannuation Rate_Base Salary + Costs_MP" in df.columns
