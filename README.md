# Microcosting Health Workforce

This project is a Python-based tool to convert an Excel file with formulae into a Python script.

## Setup

1.  **Install dependencies:**
    ```bash
    make install
    ```

2.  **Activate the virtual environment:**
    ```bash
    pipenv shell
    ```

## Usage

*   **Run tests:**
    ```bash
    make test
    ```

*   **Lint and format the code:**
    ```bash
    make lint
    make format
    ```

*   **Run type checks:**
    ```bash
    make typecheck
    ```

*   **Run security analysis:**
    ```bash
    make security
    ```

*   **Run all checks:**
    ```bash
    make all
    ```

*   **Run tests in multiple environments (requires `tox`):**
    ```bash
    tox
    ```
