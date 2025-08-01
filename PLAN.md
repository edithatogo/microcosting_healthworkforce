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

### Step 4: Implement Sensitivity Analysis

- **Goal:** Build the DSA and PSA capabilities on top of the new, flexible architecture.
- **Action:**
    - [ ] Design a module (`src/sensitivity_analysis.py`) that can interact with the formula engine.
    - [ ] For DSA, the module will iterate through a list of parameters, modifying them one by one and recording the output.
    - [ ] For PSA, the module will accept probability distributions for parameters and run Monte Carlo simulations.

---

### Documentation and Quality (Ongoing)

- [ ] All new code will be documented with docstrings.
- [ ] Tests will be written for the formula engine and sensitivity analysis modules.
- [ ] Code will be kept clean and compliant with `ruff` standards.