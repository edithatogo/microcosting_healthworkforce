import openpyxl


def list_excel_sheets(file_path: str) -> None:
    """
    Lists all the sheet names in an Excel file.
    """
    workbook = openpyxl.load_workbook(file_path, read_only=True)
    print("Sheet names:")
    for sheet_name in workbook.sheetnames:
        print(f"- {sheet_name}")


if __name__ == "__main__":
    list_excel_sheets("data/Labour Model - v3, 20240328.xlsx")
