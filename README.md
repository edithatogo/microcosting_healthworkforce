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

The base-sheet logic is implemented as three concise formulas in `data/formulas.json`:

- `annual_raw_cost`: Year 0 raw annual cost before productive time adjustment.
  - `base_salary + base_salary*(super_rate + avg_penalties + pub_holiday_penalty + private_practice_loading + retention_allowance + sick_leave) + professional_development_allowance + base_salary*((52+annual_leave_weeks)/52)*(1+annual_leave_loading)`
- `year_0_total_cost`: Adjusts the raw cost by productive time.
  - `annual_raw_cost / productive_time_factor`
- `hourly_rate`: Converts annual total cost to hourly.
  - `year_0_total_cost / 52 / hours_per_week`

Output mapping mirrors the base sheet:
- `Calculated_Cost_LL` and `Calculated_Cost_UL` are read directly from sheet columns.
- `Calculated_Cost_Mid` is computed via `year_0_total_cost` using the row’s parameters.

Note: Percentage-like inputs must be provided in consistent units (e.g., fractions such as `0.10`), and `productive_time_factor` should reflect a fraction (e.g., `0.8`).

### Base-Sheet Column Mapping
- J → `super_rate` (`Grade(s)_Superannuation Rate (%)`)
- K → `hours_per_week` (`Grade(s)_Hours per week`)
- L → `productive_time_factor` (`Grade(s)_Average productive time (%)`)
- R → `professional_development_allowance` (`Grade(s)_Professional Development Allowance ($)`)
- S → `annual_leave_weeks` (`Grade(s)_Annual Leave Entitlement (Weeks)`)
- T → `annual_leave_loading` (`Grade(s)_Annual Leave Loading (%)`)
- Base salary (LL/Mid/UL): `Base Salary_LL`, `Base Salary_Mid-point`, `Base Salary_UL`
- Total cost (LL/Mid/UL, sheet): `Base Salary + Costs_LL`, `..._Mid-point`, `..._UL`

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
