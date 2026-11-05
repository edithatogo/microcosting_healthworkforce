# Copyright 2025 doughnut. SPDX-License-Identifier: Apache-2.0
"""Configure the project Sphinx documentation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

project = "Microcosting Health Workforce"
copyright = "2025, doughnut"  # noqa: A001 - required Sphinx configuration key
author = "doughnut"
release = "0.0.1"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "furo",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns: list[str] = []

html_theme = "furo"
html_static_path = ["_static"]
