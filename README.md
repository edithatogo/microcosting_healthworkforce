# Microcosting Health Workforce

This project is a Python-based tool to translate a specific Excel cost model into a validated and maintainable Python application.

## Overview

The primary function of this application is to process the "Labour - Prices" sheet from the `data/Labour Model - v3, 20240328.xlsx` file. It performs the following key tasks:

1.  **Data Loading:** It reads the specified Excel sheet, handles its multi-level headers, and cleans the data into a structured format (a pandas DataFrame).
2.  **Cost Calculation:** It calculates the "Year 0" costs for each position listed in the sheet.
3.  **Formula Logic:** The calculation engine is designed to handle two scenarios:
    *   It applies a standard, consistent formula for most positions.
    *   It correctly uses the hardcoded override values that exist in the Excel sheet for specific generic or averaged rows.
4.  **Validation:** The script includes a validation step that compares the results of the Python calculation against the original values in the Excel file to ensure accuracy.

## Setup

1.  **Install dependencies:**
    ```bash
    make install
    ```

2.  **Activate the virtual environment:**
    ```bash
    pipenv shell
    ```

## Usage

*   **Run the main application:**
    To execute the data loading, calculation, and validation process, run the following command from the project root:
    ```bash
    PYTHONPATH=. python3 src/main.py
    ```

*   **Run tests:**
    ```bash
    make test
    ```

*   **Lint and format the code:**
    ```bash
    make lint
    make format
    ```

*   **Run type checks:**
    ```bash
    make typecheck
    ```

*   **Run security analysis:**
    ```bash
    make security
    ```

*   **Run all checks:**
    ```bash
    make all
    ```

*   **Build the documentation:**
    ```bash
    make docs
    ```

