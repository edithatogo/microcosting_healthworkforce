import openpyxl


def inspect_excel_formulas(file_path: str, sheet_name: str) -> None:
    """
    Reads an Excel file and prints the formulas from a specified sheet.
    """
    workbook = openpyxl.load_workbook(file_path, data_only=False)
    sheet = workbook[sheet_name]

    for row in sheet.iter_rows():
        for cell in row:
            if cell.data_type == "f":
                print(f"Cell {cell.coordinate}: {cell.value}")


if __name__ == "__main__":
    inspect_excel_formulas("data/Labour Model - v3, 20240328.xlsx", "Labour - Prices")
