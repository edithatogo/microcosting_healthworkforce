# Protocol for the Development of a Data-Driven Microcosting Model

**Version:** 1.0  
**Date:** 2025-08-12

---

## 1.0 Introduction and Rationale

### 1.1 Background

The accurate costing of the health workforce is a critical input for economic evaluations, budget planning, and health policy decision-making. Microcosting, a highly detailed bottom-up approach, provides the most precise estimates but is often resource-intensive and difficult to scale. Traditional spreadsheet-based models, while common, can be prone to errors, lack transparency, and are challenging to validate, maintain, and extend.

This document outlines the development protocol for a Python-based software tool designed to overcome these limitations. The project's primary goal is to create a transparent, validated, and extensible calculation engine for microcosting a health workforce, based on industrial awards and enterprise agreements.

### 1.2 Project Objectives

The core objectives of this software development project were to:

1.  **Develop a modular calculation engine:** To separate data loading, calculation logic, and reporting into distinct, manageable components.
2.  **Ensure transparency and reproducibility:** To build a system where all calculations are explicitly defined in auditable configuration files rather than being hidden in opaque spreadsheet formulas.
3.  **Implement a data-driven architecture:** To create a flexible engine capable of performing complex calculations based on externally supplied data and formula definitions.
4.  **Establish a robust validation framework:** To verify the accuracy of the model's outputs against both the original spreadsheet model and, in future phases, against source legal documents (awards and agreements).
5.  **Automate sensitivity analysis:** To integrate both Deterministic and Probabilistic Sensitivity Analysis (DSA and PSA) to allow for robust exploration of uncertainty.
6.  **Ensure code quality and maintainability:** To adhere to modern software engineering best practices, including version control, automated testing, and static analysis.

---

## 2.0 Methodology and System Design

### 2.1 System Architecture

The software is designed with a modular architecture, with components organized in the `src/` directory. This separation of concerns enhances maintainability and testability.

-   **`main.py`**: The main entry point and orchestrator of the application. It handles command-line argument parsing, logging setup, and coordinates the main workflow.
-   **`data_loader.py`**: Responsible for loading and cleaning all input data from source files (e.g., Excel spreadsheets, JSON configurations).
-   **`formula_parser.py`**: Parses the formula definitions from a JSON file.
-   **`formula_engine.py`**: The core of the calculation engine. It applies the parsed formulas to the input dataframes in a specified sequence. It uses the `asteval` library for the safe evaluation of mathematical expressions.
-   **`projection.py`**: Handles the projection of costs over a multi-year horizon.
-   **`rate_converter.py`**: Converts final calculated costs into more granular rates (e.g., hourly, daily).
-   **`calculations.py`**: Encapsulates the entire calculation pipeline, from applying base formulas to projection and rate conversion.
-   **`dsa_analysis.py` & `psa_analysis.py`**: Manage the logic for Deterministic and Probabilistic Sensitivity Analyses, respectively.
-   **`validation.py`**: Contains functions to compare model outputs against pre-calculated validation data.
-   **`reporting.py`**: Responsible for generating all outputs, including CSV files and plots (e.g., tornado plots, histograms).

### 2.2 Data-Driven Calculation

A key design principle is the decoupling of the calculation logic from the code itself.

-   **Formulas (`data/formulas.json`)**: All mathematical operations and their interdependencies are defined in a JSON file. This allows for easy auditing and modification of the calculation logic without changing the Python source code.
-   **Scenarios (`data/dsa_scenarios.json`, `data/psa_scenarios.json`)**: The parameters for sensitivity analyses are defined in separate JSON files, allowing for flexible what-if analysis.
-   **Input Data (`data/Labour Model.xlsx`)**: The primary input data is loaded from a structured Excel file, separating the core data from the calculation engine.

### 2.3 Validation Framework

Validation is a cornerstone of the methodology, designed to build confidence in the model's outputs. The protocol specifies a two-stage validation process:

1.  **Initial Validation (Complete):** The model's outputs were rigorously compared against the results from the original, manually-created Excel model. This ensured that the Python implementation correctly replicated the initial logic.
2.  **Source-of-Truth Validation (Planned):** A new validation phase is designed to compare the model's outputs against parameters and logic extracted directly from primary source documents (e.g., awards, collective agreements). This will provide a higher level of external validity.

---

## 3.0 Implementation and Quality Assurance

### 3.1 Technology Stack

-   **Programming Language:** Python 3 (tested on versions 3.9, 3.11).
-   **Core Libraries:**
    -   `pandas` & `numpy` for data manipulation and numerical operations.
    -   `openpyxl` for reading from Excel files.
    -   `asteval` for safe evaluation of formula expressions.
    -   `matplotlib` & `seaborn` for data visualization and plot generation.

### 3.2 Development Environment and Dependency Management

-   **`pipenv`**: Used for managing project dependencies and creating a consistent development environment, with dependencies specified in the `Pipfile`.
-   **`tox`**: Used for automating testing in isolated environments across multiple Python versions, ensuring compatibility. Configuration is managed in `tox.ini`.

### 3.3 Code Quality and Continuous Integration

A suite of tools and practices were employed to ensure high code quality.

-   **`pre-commit`**: The framework is used to manage and run pre-commit hooks, automating quality checks before code is committed.
-   **`ruff`**: Used for extremely fast code linting and formatting, ensuring adherence to style guides and catching common errors.
-   **`mypy`**: Used for static type checking to identify type-related errors and improve code robustness.
-   **`bandit`**: Used to perform static security analysis to find common security issues.
-   **Continuous Integration (CI):** A CI pipeline is defined in `.github/workflows/ci.yml`. This workflow automatically runs all tests, linters, and quality checks on every push and pull request to the main development branches.

### 3.4 Version Control

-   **Git & GitHub:** The project is managed using Git for version control and hosted on GitHub.
-   **Branching Strategy:** A feature-based branching strategy is used. Changes are developed in separate branches (e.g., `chore/fix-warnings`) and merged into the main branch after review.
-   **Semantic Versioning:** The project aims to follow semantic versioning for releases, with versions tagged in Git and published as GitHub Releases.

---

## 4.0 Project Management and Documentation

-   **`ROADMAP.md`**: A high-level document outlining the planned features and development phases of the project.
-   **`CHANGELOG.md`**: A log of notable changes for each version of the software.
-   **`README.md`**: The primary entry point for users and developers, providing an overview of the project, setup instructions, and usage examples.
-   **Docstrings**: All modules and functions are documented with comprehensive docstrings following standard Python conventions.
