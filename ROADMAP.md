# Project Roadmap

This document outlines the development plan for the Microcosting Health Workforce project. The immediate goal is to translate a single sheet from an Excel file into a robust and tested Python application.

## Phase 1: Setup and Analysis (Current)

- [x] Initialize project structure and CI/CD.
- [x] Define a comprehensive development plan.
- [ ] **Next:** Set up project dependencies (`pandas`, `openpyxl`).
- [ ] **Next:** Analyze the specified Excel sheet to map data structures, inputs, and formulas.

## Phase 2: Core Logic Implementation

- [ ] Develop a data loading module (`src/data_loader.py`) to read the specified sheet into a pandas DataFrame.
- [ ] Translate the sheet's Excel formulas into Python functions within a dedicated calculations module (`src/calculations.py`).
- [ ] Implement the main script (`src/main.py`) to orchestrate the data loading and calculation workflow.

## Phase 3: Validation and Testing

- [ ] Write unit tests for each calculation function to ensure correctness.
- [ ] Create an integration test to validate the end-to-end Python workflow against the original Excel sheet's results.
- [ ] Use a dedicated, non-sensitive test version of the input file for all tests.

## Phase 4: Finalization and Documentation

- [ ] Refactor the Python code for clarity, efficiency, and adherence to best practices (PEP 8, typing).
- [ ] Run linters and formatters (`ruff`) to ensure code quality.
- [ ] Add comprehensive docstrings to all new modules and functions.
- [ ] Update `README.md` with instructions on how to set up and run the project.