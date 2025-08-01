# Project TODO List

This list tracks the tasks required to translate the Excel sheet to Python.

### Phase 1: Setup and Analysis
- [ ] Add `pandas` and `openpyxl` to `Pipfile`.
- [ ] Install dependencies via `pipenv install`.
- [ ] Create `data/` directory for the input Excel file.
- [ ] Receive the name of the target Excel sheet from the user.
- [ ] Analyze the structure and formulas of the target sheet.

### Phase 2: Core Logic Implementation
- [ ] Create `src/data_loader.py`.
- [ ] Implement function in `data_loader.py` to load the specific sheet.
- [ ] Create `src/calculations.py`.
- [ ] Implement Python functions in `calculations.py` for each Excel formula.
- [ ] Update `src/main.py` to orchestrate the data loading and calculation workflow.

### Phase 3: Validation and Testing
- [ ] Create `tests/fixtures/` directory.
- [ ] Add a non-sensitive test version of the Excel file to `tests/fixtures/`.
- [ ] Create `tests/test_calculations.py`.
- [ ] Write unit tests for all functions in `src/calculations.py`.
- [ ] Update `tests/test_main.py` with an end-to-end integration test.

### Phase 4: Finalization and Documentation
- [ ] Run `ruff check .` and `ruff format .` to ensure code quality.
- [ ] Add docstrings to all new modules and functions.
- [ ] Update `README.md` with setup and usage instructions.
