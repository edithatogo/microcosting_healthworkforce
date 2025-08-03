# Development Plan

This plan outlines the next steps for the project, focusing on abstracting the core logic before implementing sensitivity analysis.

### Current Status

The initial translation of the "Labour - Prices" sheet from Excel to Python is complete. The core calculations are currently hardcoded in `src/calculations.py`.

### The Path Forward: Abstraction First

Before implementing sensitivity analysis (DSA/PSA), we will abstract the formula logic. This will create a flexible and scalable foundation, preventing significant rework later.

---

### Step 1: Design the Formula Data Structure

- **Goal:** Define a clear, machine-readable structure for representing formulas.
- **Considerations:**
    - The structure must support variables, parameters, and mathematical operations.
    - It should be extensible for future formula types.
    - A `JSON` or `YAML` file is a likely candidate for storing this data.
- **Action:**
    - [ ] Draft a schema for the formula structure.
    - [ ] Create a sample `formulas.json` (or similar) file representing one or two of the existing calculations.

---

### Step 2: Build the Formula Engine

- **Goal:** Create a Python module that can parse the data structure and execute the calculations.
- **Action:**
    - [ ] Create `src/formula_engine.py`.
    - [ ] Write a function to load and validate the `formulas.json` file.
    - [ ] Implement a core function that takes the formula definition and input data, then returns the result.
    - [ ] This engine will replace the hardcoded functions in `src/calculations.py`.

---

### Step 3: Refactor Main Workflow

- **Goal:** Integrate the new formula engine into the main application.
- **Action:**
    - [ ] Update `src/main.py` to use `src/formula_engine.py` instead of `src/calculations.py`.
    - [ ] Remove the old, hardcoded functions from `src/calculations.py`, or deprecate the file entirely.
    - [ ] Ensure the final output still matches the validated results from the original Excel sheet.

---

### Step 4: Implement Deterministic Sensitivity Analysis (DSA)

- **Goal:** Build the DSA capability on top of the new, flexible architecture to systematically test the impact of changing single parameters.
- **Action:**
    - [ ] **Create Scenario Definition File:**
        - Create `data/dsa_scenarios.json`.
        - This file will contain a list of scenarios, each specifying the `parameter_to_vary`, the `variation` type (`percentage` or `absolute`), and the `value`.
    - [ ] **Build the DSA Engine (`src/sensitivity_analysis.py`):**
        - Create a `run_dsa` function that loads scenarios from the JSON file.
        - The function will iterate through each scenario, apply the variation to a copy of the data, and re-run the full calculation pipeline (`formula_engine` -> `projection` -> `rate_converter`).
    - [ ] **Implement Flexible Overrides:**
        - The `run_dsa` function will accept an optional `custom_scenarios` argument to allow for runtime-defined analyses.
        - This custom scenario structure will support an optional `row_filter` key to allow variations to be applied to all rows (globally) or only to a specific subset of rows.
    - [ ] **Integrate into Main Workflow:**
        - Add a mechanism in `src/main.py` to trigger the DSA run and report the results, comparing each scenario's output to the base case.

---

### Step 5: Implement Probabilistic Sensitivity Analysis (PSA) (Future)

- **Goal:** Build the PSA capability to analyze the impact of varying multiple parameters simultaneously based on probability distributions.
- **Action:**
    - [ ] For PSA, the module will accept probability distributions for parameters and run Monte Carlo simulations.

---

### Documentation and Quality (Ongoing)

- [ ] All new code will be documented with docstrings.
- [ ] Tests will be written for the formula engine and sensitivity analysis modules.
- [ ] Code will be kept clean and compliant with `ruff` standards.