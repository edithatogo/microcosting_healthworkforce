import os
import sys

sys.path.insert(0, os.path.abspath("../../src"))

project = "Microcosting Health Workforce"
copyright = "2025, doughnut"
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
