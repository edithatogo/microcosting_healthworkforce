# Project Roadmap

This document outlines the development plan for the Microcosting Health Workforce project.

## Phase 1: Core Logic Implementation (Complete)

- [x] Set up project dependencies (`pandas`, `openpyxl`).
- [x] Analyze the "Labour - Prices" Excel sheet to map data structures and formulas.
- [x] Develop a data loading module (`src/data_loader.py`) to read and clean the sheet.
- [x] Translate the "Year 0" Excel formulas into Python functions in `src/calculations.py`.
- [x] Implement logic to handle both standard formulas and hardcoded overrides.
- [x] Implement the main script (`src/main.py`) to orchestrate the workflow.
- [x] Validate the Python output against the original Excel file.

## Phase 2: Formula Abstraction (Complete)

- [x] **Goal:** Abstract the calculation logic to be data-driven rather than hardcoded in Python. This is a prerequisite for robust sensitivity analysis.
- [x] **Tasks:**
    - [x] Design a data structure (e.g., JSON, YAML, or a database schema) to define formulas, parameters, and their relationships.
    - [x] Refactor the calculation engine to interpret these formula definitions dynamically.
    - [x] This will allow for different formulas for each position and jurisdiction without changing the Python code.

## Phase 3: Sensitivity Analysis (Complete)

- [x] **Goal:** Implement Deterministic and Probabilistic Sensitivity Analysis (DSA & PSA).
- [x] **Prerequisite:** Completion of Phase 2: Formula Abstraction.
- [x] **Tasks:**
    - [x] Develop a module to systematically vary input parameters defined in the new data-driven formula structure.
    - [x] Implement DSA to analyze the impact of changing one parameter at a time.
    - [x] Implement PSA to analyze the impact of varying multiple parameters simultaneously based on probability distributions.

## Phase 4: Code Refactoring (Complete)

- [x] **Goal:** Improve the clarity, efficiency, and maintainability of the codebase.
- [x] **Tasks:**
    - [x] Centralize configuration into a single `src/config.py` file.
    - [x] Reduce code duplication in `src/data_loader.py`.
    - [x] Improve readability of `src/main.py` and `src/formula_engine.py`.
    - [x] Implement a consistent logging strategy.

## Phase 5: Finalization and Documentation (Complete)

- [x] Run linters and formatters (`ruff`) to ensure code quality.
- [x] Add comprehensive docstrings to all new modules and functions.
- [x] Update `README.md` with instructions on how to set up and run the project.

## Phase 6: Reporting and Visualization (Complete)

- [x] **Goal:** Develop a dedicated reporting module to save all outputs as files and create visualizations.
- [x] **Tasks:**
    - [x] Create a new `src/reporting.py` module.
    - [x] **File Outputs:**
        - [x] Implement functions to save the full base case results to a CSV file.
        - [x] Implement functions to save the detailed DSA results (one file per scenario) and a summary table to CSV.
        - [x] Implement functions to save the raw PSA iteration results to a CSV file.
    - [x] **Visualizations:**
        - [x] Add `matplotlib` and `seaborn` as project dependencies.
        - [x] For DSA, generate and save a tornado plot summarizing the most sensitive parameters.
        - [x] For PSA, generate and save a histogram (distribution plot) of the simulation outcomes.
    - [x] **Integration:**
        - [x] Integrate the new reporting functions into the `src/main.py` workflow.
        - [x] Add command-line arguments to control output generation (e.g., `--output-dir`).