# tests/test_formula_parser.py
"""
Tests for the formula_parser module.
"""

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
    Tests that the evaluate_expression function raises a NameError when a
    variable is not defined.
    """
    expression = "a + b"
    parameters = {"a": 1}
    try:
        evaluate_expression(expression, parameters)
    except Exception as e:
        assert "is not defined" in str(e)


def test_evaluate_expression_syntax_error() -> None:
    """
    Tests that the evaluate_expression function raises a SyntaxError when the
    expression is invalid.
    """
    expression = "a + "
    parameters = {"a": 1}
    try:
        evaluate_expression(expression, parameters)
    except Exception as e:
        assert "invalid syntax" in str(e)
