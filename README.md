# Microcosting Health Workforce

This project is a Python-based tool to translate a specific Excel cost model into a validated, maintainable, and data-driven Python application.

## Overview

The primary function of this application is to process the "Labour - Prices" sheet from the `data/Labour Model - v3, 20240328.xlsx` file. It performs the following key tasks:

1.  **Data Loading:** It reads the specified Excel sheet, handles its multi-level headers, and cleans the data into a structured pandas DataFrame.
2.  **Data-Driven Calculation:** It uses a formula engine that dynamically calculates costs based on definitions in `data/formulas.json`. This approach allows for easy modification and extension of formulas without changing the core Python code.
3.  **Formula Logic:** The engine handles two scenarios:
    *   It applies standard, defined formulas for most positions.
    *   It correctly uses hardcoded override values from the original Excel sheet for specific generic or averaged rows.
4.  **Multi-Year Projections:** The tool projects costs into the future based on a defined indexation rate, allowing for sophisticated long-term financial analysis.
5.  **Rate Conversion:** After calculating the annual costs, it converts them into multiple time-based rates (hourly, daily, weekly, etc.) for flexible reporting.
6.  **Validation:** The script includes a validation step that compares the results of the Python calculation against the original values in the Excel file to ensure accuracy for the baseline year.

## Analytical Capabilities

Beyond simple cost translation, this tool is designed to support advanced analysis:

-   **Budget Impact Analysis:** Understand the financial implications of workforce changes over time.
-   **Long-Term Financial Forecasting:** Model total workforce costs over a multi-year horizon for strategic planning.
-   **Cost-Effectiveness Analysis (CEA):** Provide foundational cost data for health economics models that compare different interventions.
-   **Scenario & "What-If" Planning:** Easily model the financial impact of changes in indexation rates, staffing levels, or workforce composition.
-   **Deterministic Sensitivity Analysis (DSA):** Systematically analyze the impact of changing a single input parameter (e.g., "Superannuation Rate +/- 10%") on the final costs to identify the most influential variables in the model.

## Core Components

-   `src/main.py`: The main entry point that orchestrates the data loading, calculation, and validation process.
-   `src/data_loader.py`: Handles reading and cleaning the Excel data.
-   `src/formula_engine.py`: Calculates the foundational "Year 0" annual costs based on definitions in `data/formulas.json`.
-   `src/projection.py`: Takes the Year 0 costs and projects them into the future.
-   `src/rate_converter.py`: Converts annual costs for each year into time-based rates.
-   `src/sensitivity_analysis.py`: Runs Deterministic Sensitivity Analysis (DSA) based on scenarios defined in `data/dsa_scenarios.json`.
-   `src/formula_parser.py`: Safely evaluates the mathematical expressions defined in the formulas.
-   `data/formulas.json`: A JSON file that defines the parameters, expressions, and output mappings for all calculations.
-   `data/dsa_scenarios.json`: Defines the scenarios (e.g., parameter to vary, amount of variation) to be run by the DSA module.

## Formulas

The calculation engine is driven by the formulas defined in `data/formulas.json`. These formulas are used to calculate the total cost for each position. The following formulas are currently implemented:

-   **`base_salary_with_super`**: Calculates the base salary including superannuation.
    -   `base_salary * (1 + super_rate)`
-   **`total_penalties`**: Calculates the total penalties.
    -   `base_salary * (avg_penalties + pub_holiday_penalty + private_practice_loading)`
-   **`total_allowances`**: Calculates the total allowances.
    -   `base_salary * retention_allowance + professional_development_allowance`
-   **`total_leave_costs`**: Calculates the total leave costs.
    -   `base_salary * sick_leave + (base_salary * (annual_leave_weeks / 52) * annual_leave_loading)`
-   **`year_0_total_cost`**: Calculates the total annual cost for a single position.
    -   `(base_salary_with_super + total_penalties + total_allowances + total_leave_costs) / productive_time_factor`

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
