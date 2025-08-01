# Microcosting Health Workforce

This project is a Python-based tool to translate a specific Excel cost model into a validated, maintainable, and data-driven Python application.

## Overview

The primary function of this application is to process the "Labour - Prices" sheet from the `data/Labour Model - v3, 20240328.xlsx` file. It performs the following key tasks:

1.  **Data Loading:** It reads the specified Excel sheet, handles its multi-level headers, and cleans the data into a structured pandas DataFrame.
2.  **Data-Driven Calculation:** It uses a formula engine that dynamically calculates costs based on definitions in `data/formulas.json`. This approach allows for easy modification and extension of formulas without changing the core Python code.
3.  **Formula Logic:** The engine handles two scenarios:
    *   It applies standard, defined formulas for most positions.
    *   It correctly uses hardcoded override values from the original Excel sheet for specific generic or averaged rows.
4.  **Validation:** The script includes a validation step that compares the results of the Python calculation against the original values in the Excel file to ensure accuracy.

## Core Components

-   `src/main.py`: The main entry point that orchestrates the data loading, calculation, and validation process.
-   `src/data_loader.py`: Handles reading and cleaning the Excel data.
-   `src/formula_engine.py`: Loads formula definitions and applies them to the data.
-   `src/formula_parser.py`: Safely evaluates the mathematical expressions defined in the formulas.
-   `data/formulas.json`: A JSON file that defines the parameters, expressions, and output mappings for all calculations.

## Setup

1.  **Prerequisites:**
    -   Python 3.10+
    -   `pipenv`

2.  **Install dependencies:**
    This project uses `pipenv` to manage dependencies, which include `pandas`, `openpyxl`, and `asteval`.
    ```bash
    make install
    ```

3.  **Activate the virtual environment:**
    ```bash
    pipenv shell
    ```

## Usage

-   **Run the main application:**
    To execute the data loading, calculation, and validation process, run the following command from the project root:
    ```bash
    PYTHONPATH=. python3 src/main.py
    ```

-   **Run tests:**
    ```bash
    make test
    ```

-   **Lint and format the code:**
    ```bash
    make lint
    make format
    ```

-   **Run all checks (lint, format, type-check, security):**
    ```bash
    make all
    ```

-   **Build the documentation:**
    The documentation is built using Sphinx.
    ```bash
    make docs
    ```
    The output will be in the `docs/_build/html` directory.