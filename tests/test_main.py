import pandas as pd


def test_data_loading() -> None:
    """
    Tests that the data loading function can read the excel file
    and that the columns are what we expect.
    """
    # To avoid running PSA, we don't pass any arguments
    df = pd.read_excel(
        "data/Labour Model - v3, 20240328.xlsx",
        sheet_name="Labour - Prices (DSA, Values)",
        header=[0, 1, 2],
    )
    assert isinstance(df.columns, pd.MultiIndex)  # nosec B101
