# Development Plan: Excel to Python Translation

This document details the plan for translating a single sheet of an Excel workbook into a Python application.

### Guiding Principles

*   **Single Responsibility:** Each part of the code (data loading, calculations) will be in its own module. Functions will be small and focused.
*   **Test-Driven:** Development will be guided by tests to ensure the Python implementation is accurate and reliable.
*   **Maintainability:** The code will be clean, well-documented, and easy to understand for future development.

---

### Phase 1: Setup and Analysis

1.  **Dependencies:**
    *   The `Pipfile` will be updated to include `pandas` for data manipulation and `openpyxl` for reading the Excel file.
2.  **Project Structure:**
    *   `data/`: This directory will hold the input Excel file.
    *   `src/`: Will contain the core Python logic.
    *   `tests/`: Will contain all tests.
3.  **Excel Sheet Analysis:**
    *   Before coding, the target sheet will be analyzed to:
        *   Identify all input cells and data ranges.
        *   Trace the logic of all formulas.
        *   Understand the data flow from input to final output.
    *   **Constraint:** Only one sheet will be translated. All other sheets in the Excel file will be ignored.

---

### Phase 2: Core Logic Implementation

1.  **Data Loading (`src/data_loader.py`):**
    *   A function will be created to load the specified Excel sheet into a pandas DataFrame. This function will be configurable to easily change the file path or sheet name.
2.  **Calculations (`src/calculations.py`):**
    *   Each distinct formula from the Excel sheet will be translated into a corresponding Python function.
    *   Pandas operations (`merge`, boolean indexing, etc.) will be used to replicate Excel functions like `VLOOKUP`, `SUMIF`, etc.
3.  **Main Script (`src/main.py`):**
    *   This script will serve as the entry point, orchestrating the workflow:
        1.  Load data using the `data_loader` module.
        2.  Execute calculations using the `calculations` module.
        3.  Produce a final output, likely a pandas DataFrame, which can be saved to a file.

---

### Phase 3: Validation and Testing

1.  **Test Data:**
    *   A small, non-sensitive version of the Excel file will be placed in `tests/fixtures/` to be used as a reliable test input.
2.  **Unit Tests (`tests/test_calculations.py`):**
    *   Each function in `src/calculations.py` will have a unit test to verify its correctness against a known result from Excel.
3.  **Integration Test (`tests/test_main.py`):**
    *   A test will be created to run the entire process from start to finish and compare the final Python output with the final Excel output.

---

### Phase 4: Finalization and Documentation

1.  **Code Quality:**
    *   The codebase will be linted and formatted with `ruff`.
    *   Type hints will be used to support static analysis with `mypy`.
2.  **Documentation:**
    *   All new modules and functions will have clear docstrings.
    *   The `README.md` will be updated to explain how to install dependencies and run the application.
