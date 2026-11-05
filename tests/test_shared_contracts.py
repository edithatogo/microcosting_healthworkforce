# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Check strict formula contracts and scenario mapping compatibility."""

import pytest
from pydantic import ValidationError

from src.contracts import FORMULA_ADAPTER, parameter_mapping
from tests.checks import assert_that


def test_formula_metadata_is_preserved() -> None:
    """Preserve extended metadata without coercing parameter declarations."""
    source = {
        "formulas": [{"id": "x", "expression": "a", "parameters": ["a"]}],
        "outputs": [
            {"name": "x", "calculation_method": "direct", "source_column": "a"},
        ],
        "reference": {"edition": "synthetic"},
    }
    assert_that(FORMULA_ADAPTER.validate_python(source) == source)
    with pytest.raises(ValidationError):
        FORMULA_ADAPTER.validate_python({"formulas": "invalid", "outputs": []})


def test_parameter_mapping_retains_order_and_rejects_coercion() -> None:
    """Keep last-declared mapping precedence and reject non-string columns."""
    source = {
        "outputs": [
            {"parameter_mapping": {"a": "first"}},
            {"parameter_mapping": {"a": "last", "b": "second"}},
        ],
    }
    assert_that(parameter_mapping(source) == {"a": "last", "b": "second"})
    assert_that(parameter_mapping({}) == {})
    with pytest.raises(ValidationError):
        parameter_mapping({"outputs": [{"parameter_mapping": {"a": 2}}]})
