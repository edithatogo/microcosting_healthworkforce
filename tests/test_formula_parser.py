# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
# tests/test_formula_parser.py
"""Test for the formula_parser module."""

import pytest

from src.formula_parser import evaluate_expression
from tests.checks import assert_that

EXPECTED_3 = 3


def test_evaluate_expression_success() -> None:
    """Evaluate valid arithmetic using the supplied variables."""
    expression = "a + b"
    parameters = {"a": 1, "b": 2}
    assert_that(evaluate_expression(expression, parameters) == EXPECTED_3)


def test_evaluate_expression_name_error() -> None:
    """Reject an expression containing an undefined variable."""
    expression = "a + b"
    parameters = {"a": 1}
    # Use a raw string (r"...") for the regex to avoid syntax warnings
    with pytest.raises(ValueError, match=r"Error in expression 'a \+ b'"):
        evaluate_expression(expression, parameters)


def test_evaluate_expression_syntax_error() -> None:
    """Reject an expression with invalid syntax."""
    expression = "a + "
    parameters = {"a": 1}
    with pytest.raises(ValueError, match=r"Error in expression 'a \+ '"):
        evaluate_expression(expression, parameters)


def test_evaluate_expression_division_by_zero() -> None:
    """Reject division by zero."""
    expression = "a / b"
    parameters = {"a": 1, "b": 0}
    with pytest.raises(ValueError, match=r"Error in expression 'a / b'"):
        evaluate_expression(expression, parameters)
