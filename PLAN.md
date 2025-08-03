# Development Plan

This plan outlines the next steps for the project, focusing on abstracting the core logic before implementing sensitivity analysis.

### Current Status

This document is for historical reference. The development has progressed significantly beyond this initial plan. All major features outlined below, including the formula engine, DSA, and PSA, have been implemented. The `ROADMAP.md` provides a high-level overview of the completed phases, and the `README.md` describes the current, fully-featured state of the application.

### The Path Forward: Abstraction First (Completed)

Before implementing sensitivity analysis (DSA/PSA), we will abstract the formula logic. This will create a flexible and scalable foundation, preventing significant rework later.

---

### Step 1: Design the Formula Data Structure (Completed)

- **Goal:** Define a clear, machine-readable structure for representing formulas.
- **Considerations:**
    - The structure must support variables, parameters, and mathematical operations.
    - It should be extensible for future formula types.
    - A `JSON` or `YAML` file is a likely candidate for storing this data.
- **Action:**
    - [x] Draft a schema for the formula structure.
    - [x] Create a sample `formulas.json` (or similar) file representing one or two of the existing calculations.

---

### Step 2: Build the Formula Engine (Completed)

- **Goal:** Create a Python module that can parse the data structure and execute the calculations.
- **Action:**
    - [x] Create `src/formula_engine.py`.
    - [x] Write a function to load and validate the `formulas.json` file.
    - [x] Implement a core function that takes the formula definition and input data, then returns the result.
    - [x] This engine will replace the hardcoded functions in `src/calculations.py`.

---

### Step 3: Refactor Main Workflow (Completed)

- **Goal:** Integrate the new formula engine into the main application.
- **Action:**
    - [x] Update `src/main.py` to use `src/formula_engine.py` instead of `src/calculations.py`.
    - [x] Remove the old, hardcoded functions from `src/calculations.py`, or deprecate the file entirely.
    - [x] Ensure the final output still matches the validated results from the original Excel sheet.

---

### Step 4: Implement Deterministic Sensitivity Analysis (DSA) (Completed)

- **Goal:** Build the DSA capability on top of the new, flexible architecture to systematically test the impact of changing single parameters.
- **Action:**
    - [x] **Create Scenario Definition File:**
        - Create `data/dsa_scenarios.json`.
        - This file will contain a list of scenarios, each specifying the `parameter_to_vary`, the `variation` type (`percentage` or `absolute`), and the `value`.
    - [x] **Build the DSA Engine (`src/sensitivity_analysis.py`):**
        - Create a `run_dsa` function that loads scenarios from the JSON file.
        - The function will iterate through each scenario, apply the variation to a copy of the data, and re-run the full calculation pipeline (`formula_engine` -> `projection` -> `rate_converter`).
    - [x] **Implement Flexible Overrides:**
        - The `run_dsa` function will accept an optional `custom_scenarios` argument to allow for runtime-defined analyses.
        - This custom scenario structure will support an optional `row_filter` key to allow variations to be applied to all rows (globally) or only to a specific subset of rows.
    - [x] **Integrate into Main Workflow:**
        - Add a mechanism in `src/main.py` to trigger the DSA run and report the results, comparing each scenario's output to the base case.

---

### Step 5: Implement Probabilistic Sensitivity Analysis (PSA) (Future) (Completed)

- **Goal:** Build the PSA capability to analyze the impact of varying multiple parameters simultaneously based on probability distributions.
- **Action:**
    - [x] For PSA, the module will accept probability distributions for parameters and run Monte Carlo simulations.

---

### Documentation and Quality (Ongoing)

- [x] All new code will be documented with docstrings.
- [x] Tests will be written for the formula engine and sensitivity analysis modules.
- [x] Code will be kept clean and compliant with `ruff` standards.