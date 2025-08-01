import pandas as pd


def inspect_raw_headers(file_path, sheet_name):
    """
    Reads the first 10 rows of an Excel sheet without header processing
    to inspect the raw multi-level header structure.
    """
    try:
        # Read the top 10 rows, without assuming any header row.
        # This gives us a raw look at the data.
        df_raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=10)
        
        # Convert to a format that is easy to print and inspect.
        print("Raw header structure (first 10 rows):")
        print(df_raw.to_string())

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    file_path = "data/Labour Model - v3, 20240328.xlsx"
    sheet_name = "Labour - Prices"
    inspect_raw_headers(file_path, sheet_name)
