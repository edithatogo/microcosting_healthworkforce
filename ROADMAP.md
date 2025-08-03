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

## Phase 2: Formula Abstraction (In Progress)

- [ ] **Goal:** Abstract the calculation logic to be data-driven rather than hardcoded in Python. This is a prerequisite for robust sensitivity analysis.
- [ ] **Tasks:**
    - [ ] Design a data structure (e.g., JSON, YAML, or a database schema) to define formulas, parameters, and their relationships.
    - [ ] Refactor the calculation engine to interpret these formula definitions dynamically.
    - [ ] This will allow for different formulas for each position and jurisdiction without changing the Python code.

## Phase 3: Sensitivity Analysis (Future)

- [ ] **Goal:** Implement Deterministic and Probabilistic Sensitivity Analysis (DSA & PSA).
- [ ] **Prerequisite:** Completion of Phase 2: Formula Abstraction.
- [ ] **Tasks:**
    - [ ] Develop a module to systematically vary input parameters defined in the new data-driven formula structure.
    - [ ] Implement DSA to analyze the impact of changing one parameter at a time.
    - [ ] Implement PSA to analyze the impact of varying multiple parameters simultaneously based on probability distributions.

## Phase 4: Finalization and Documentation (Ongoing)

- [ ] Refactor the Python code for clarity, efficiency, and adherence to best practices.
- [ ] Run linters and formatters (`ruff`) to ensure code quality.
- [ ] Add comprehensive docstrings to all new modules and functions.
- [ ] Update `README.md` with instructions on how to set up and run the project.