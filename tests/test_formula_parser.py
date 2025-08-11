# tests/test_formula_parser.py
"""
Tests for the formula_parser module.
"""

import pytest

from src.formula_parser import evaluate_expression


def test_evaluate_expression_success() -> None:
    """
    Tests that the evaluate_expression function correctly evaluates a valid
    expression.
    """
    expression = "a + b"
    parameters = {"a": 1, "b": 2}
    assert evaluate_expression(expression, parameters) == 3


def test_evaluate_expression_name_error() -> None:
    """
    Tests that the evaluate_expression function raises a ValueError for an
    undefined variable.
    """
    expression = "a + b"
    parameters = {"a": 1}
    # Use a raw string (r"...") for the regex to avoid syntax warnings
    with pytest.raises(ValueError, match=r"Error in expression 'a \+ b'"):
        evaluate_expression(expression, parameters)


def test_evaluate_expression_syntax_error() -> None:
    """
    Tests that the evaluate_expression function raises a ValueError for invalid
    syntax.
    """
    expression = "a + "
    parameters = {"a": 1}
    with pytest.raises(ValueError, match=r"Error in expression 'a \+ '"):
        evaluate_expression(expression, parameters)


def test_evaluate_expression_division_by_zero() -> None:
    """
    Tests that the evaluate_expression function raises a ValueError for
    division by zero.
    """
    expression = "a / b"
    parameters = {"a": 1, "b": 0}
    with pytest.raises(ValueError, match=r"Error in expression 'a / b'"):
        evaluate_expression(expression, parameters)
