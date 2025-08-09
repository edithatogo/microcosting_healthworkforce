import pandas as pd


def inspect_raw_headers(file_path: str, sheet_name: str) -> None:
    """
    Reads the first 10 rows of an Excel sheet without header processing
    to inspect the raw multi-level header structure.
    """
    try:
        # Read the top 10 rows, without assuming any header row.
        # This gives us a raw look at the data.
        df_raw: pd.DataFrame = pd.read_excel(
            file_path, sheet_name=sheet_name, header=None, nrows=10
        )

        # Convert to a format that is easy to print and inspect.
        print("Raw header structure (first 10 rows):")
        print(df_raw.to_string())

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    from src.data_loader import load_and_clean_data

    df = load_and_clean_data("data/Labour Model - v3, 20240328.xlsx", "Labour - Prices")
    print(df.head().to_string())
