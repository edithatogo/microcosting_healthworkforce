# Microcosting Health Workforce Model

This project is a Python-based tool designed to translate a complex, multi-sheet Excel cost model into a validated, maintainable, and data-driven Python application. It provides a robust platform for health economics analysis, including cost forecasting, scenario planning, and sensitivity analysis.

## Overview

The application processes the "Labour - Prices" sheet from the source Excel file, performing the following key tasks:

1.  **Data Loading and Cleaning:** It reads the specified Excel sheet, intelligently handles its multi-level headers, and cleans the data into a structured pandas DataFrame, correcting for common data entry issues.
2.  **Data-Driven Calculation Engine:** It uses a powerful formula engine that dynamically calculates costs based on definitions in `data/formulas.json`. This allows for easy modification and extension of formulas without changing the core Python code.
3.  **Flexible Formula Logic:** The engine is designed to handle multiple calculation scenarios, including applying standard formulas for most positions while correctly using hardcoded override values for specific generic or averaged rows, mirroring the logic of the original Excel model.
4.  **Multi-Year Projections:** The tool projects costs into the future based on a defined indexation rate, allowing for sophisticated long-term financial analysis and planning.
5.  **Granular Rate Conversion:** After calculating the annual costs, it converts them into multiple time-based rates (hourly, daily, weekly, etc.) for flexible reporting and analysis.
6.  **Rigorous Validation:** The script includes a comprehensive validation suite that compares the results of the Python calculation against the original values in the Excel file to ensure accuracy for both the baseline year and all sensitivity analysis scenarios.

## Analytical Capabilities

Beyond simple cost translation, this tool is designed to support advanced health economics analysis:

-   **Budget Impact Analysis:** Understand the financial implications of workforce changes over time.
-   **Long-Term Financial Forecasting:** Model total workforce costs over a multi-year horizon for strategic planning.
-   **Cost-Effectiveness Analysis (CEA):** Provide foundational cost data for health economics models that compare different interventions.
-   **"What-If" Scenario Planning:** Easily model the financial impact of changes in indexation rates, staffing levels, or workforce composition by defining custom scenarios.
-   **Deterministic Sensitivity Analysis (DSA):** Systematically analyze the impact of changing one or more input parameters (e.g., "Superannuation Rate +/- 10%") on the final costs to identify the most influential variables in the model.
-   **Probabilistic Sensitivity Analysis (PSA):** Run Monte Carlo simulations to analyze the impact of varying multiple parameters simultaneously based on probability distributions, providing a comprehensive view of model uncertainty.

## Core Components

-   `src/main.py`: The main entry point that orchestrates the data loading, calculation, and validation process.
-   `src/data_loader.py`: Handles reading and cleaning the Excel data.
-   `src/formula_engine.py`: Calculates the foundational "Year 0" annual costs based on definitions in `data/formulas.json`.
-   `src/projection.py`: Takes the Year 0 costs and projects them into the future.
-   `src/rate_converter.py`: Converts annual costs for each year into time-based rates.
-   `src/dsa_analysis.py`: Runs Deterministic Sensitivity Analysis (DSA).
-   `src/psa_analysis.py`: Runs Probabilistic Sensitivity Analysis (PSA).
-   `src/formula_parser.py`: Safely evaluates the mathematical expressions defined in the formulas.
-   `src/reporting.py`: Saves all tabular and graphical outputs to files.
-   `src/validation.py`: Compares model outputs against trusted values from the original Excel file.
-   `data/formulas.json`: Defines the parameters, expressions, and output mappings for all calculations.
-   `data/dsa_scenarios.json`: Defines the scenarios for the DSA module.
-   `data/psa_scenarios.json`: Defines the parameters and distributions for the PSA module.

## Setup

1.  **Prerequisites:**
    -   Python 3.9+
    -   `pipenv`

2.  **Install dependencies:**
    This project uses `pipenv` to manage dependencies. To install them, run:
    ```bash
    pipenv install --dev
    ```

3.  **Activate the virtual environment:**
    ```bash
    pipenv shell
    ```

## Usage

### Running the Model

The main script provides several command-line arguments to control the execution.

-   **Run the base case analysis:**
    This will run the standard calculation pipeline, validate the results, and save the output to `base_case_results.csv`.
    ```bash
    python src/main.py --output-dir ./outputs
    ```

-   **Run Deterministic Sensitivity Analysis (DSA):**
    This will run the scenarios defined in `data/dsa_scenarios.json`.
    ```bash
    python src/main.py --output-dir ./outputs
    ```
    To use a custom scenario file:
    ```bash
    python src/main.py --dsa-scenarios /path/to/your/scenarios.json --output-dir ./outputs
    ```

-   **Run Probabilistic Sensitivity Analysis (PSA):**
    This will run a Monte Carlo simulation with the parameters defined in `data/psa_scenarios.json`.
    ```bash
    python src/main.py --run-psa --output-dir ./outputs
    ```
    You can control the number of iterations:
    ```bash
    python src/main.py --run-psa --psa-iterations 5000 --output-dir ./outputs
    ```

### Interpreting the Outputs

When you run the model with the `--output-dir` flag, the following files will be generated in the specified directory:

-   `base_case_results.csv`: The full, detailed output of the standard calculation, including all cost projections and rate conversions for every position.
-   `dsa_summary.csv`: A summary table showing the percentage impact of each DSA scenario on the average cost.
-   `dsa_tornado_plot.png`: A visualization of the DSA summary, making it easy to see which parameters have the most significant impact on the results.
-   `dsa_detailed/`: A directory containing a separate, detailed CSV file for each DSA scenario that was run.
-   `psa_results.csv`: The raw output of the PSA, containing the calculated mean cost for each iteration of the simulation.
-   `psa_histogram.png`: A plot showing the distribution of the PSA results, which helps in understanding the model's uncertainty.

### Development Tasks

-   **Run tests:**
    ```bash
    tox
    ```

-   **Lint and format the code:**
    ```bash
    ruff format .
    ruff check . --fix
    ```

-   **Build the documentation:**
    The documentation is built using Sphinx.
    ```bash
    make -C docs html
    ```
    The output will be in the `docs/_build/html` directory.
