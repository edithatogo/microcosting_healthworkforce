# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Updated `src/rate_converter.py` to process multi-year projected costs, calculating rates for each year.
- Expanded `src/rate_converter.py` to calculate daily, weekly, fortnightly, and monthly rates in addition to hourly rates.
- Refactored the rate conversion logic out of `src/main.py` and into the new `src/rate_converter.py` module, cleaning up the main workflow.
- Integrated the new formula engine into `src/main.py`. The application now uses the data-driven approach defined in `data/formulas.json` to perform calculations.
- Implemented the core logic in `src/formula_engine.py` to apply formulas to the dataset.

### Added
- Created `src/projection.py` to handle multi-year cost projections based on an indexation rate.
- Created `src/rate_converter.py` to handle the conversion of annual costs to time-based rates (e.g., hourly), separating conversion logic from core cost calculation.
- Created `src/formula_engine.py` to load and orchestrate data-driven calculations.
- Created `src/formula_parser.py` to safely evaluate mathematical expressions from the formula definitions.
- Created `data/formulas.json` to begin abstracting the calculation logic. This file defines the parameters and mathematical expressions for the core cost calculation, moving the logic out of the Python code.

### Removed
- Deleted the old, hardcoded `src/calculations.py` module, as it has been replaced by the new formula engine.

### Documentation
- Updated `README.md` to include details on the multi-year projection capabilities.
- Updated `README.md` to reflect the new formula engine architecture, dependencies, and usage instructions.

### Dependencies
- Added the `asteval` library for safely evaluating mathematical expressions.



