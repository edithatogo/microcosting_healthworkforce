# Contributing

Contributions are welcome! Please follow these guidelines to contribute to the project.

## Development

1.  **Fork the repository.**
2.  **Clone your fork:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/microcosting_healthworkforce.git
    ```
3.  **Install dependencies:**
    ```bash
    make install
    ```
4.  **Create a new branch:**
    ```bash
    git checkout -b my-feature-branch
    ```
5.  **Make your changes.**
6.  **Run all checks:**
    ```bash
    make all
    ```
7.  **Commit your changes:**
    ```bash
    git commit -m "Feat: add my new feature"
    ```
8.  **Push to your fork:**
    ```bash
    git push origin my-feature-branch
    ```
9.  **Create a pull request.**

## Issues

Please use the issue templates to report bugs or request features.

## Code of Conduct

Please note that this project is released with a Contributor Code of Conduct. By participating in this project you agree to abide by its terms.

## Maintainer checks

Use Python 3.15.2 through the repo-local environment: `make install`, then verify
`.venv/bin/python --version` and run `make all`. Keep ordinary Git hooks enabled.
Use Conventional Commits, for example `fix: reject incomplete scenario inputs`.
See [quality gates](docs/quality.md) for bounded mutation tests and exclusions,
[security policy](SECURITY.md) for private reporting, and [AGENTS.md](AGENTS.md)
for repository layout and automation guidance. Never commit private workbooks,
validation receipts, credentials or generated research outputs as new fixtures.
