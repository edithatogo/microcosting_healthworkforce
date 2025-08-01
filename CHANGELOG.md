# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Integrated the new formula engine into `src/main.py`. The application now uses the data-driven approach defined in `data/formulas.json` to perform calculations.
- Implemented the core logic in `src/formula_engine.py` to apply formulas to the dataset.

### Added
- Created `src/formula_engine.py` to load and orchestrate data-driven calculations.
- Created `src/formula_parser.py` to safely evaluate mathematical expressions from the formula definitions.
- Created `data/formulas.json` to begin abstracting the calculation logic. This file defines the parameters and mathematical expressions for the core cost calculation, moving the logic out of the Python code.

### Removed
- Deleted the old, hardcoded `src/calculations.py` module, as it has been replaced by the new formula engine.

### Dependencies
- Added the `asteval` library for safely evaluating mathematical expressions.



