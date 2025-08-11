# src/formula_parser.py
"""
This module is responsible for parsing and evaluating the mathematical
expressions defined in the formula configuration. It safely evaluates
the expressions using a controlled environment to prevent security risks.
"""

from typing import Any, Dict

from asteval import Interpreter


def evaluate_expression(expression: str, parameters: Dict[str, Any]) -> Any:
    """
    Safely evaluates a mathematical expression with a given set of parameters.

    Args:
        expression: The mathematical expression string to evaluate.
        parameters: A dictionary of parameter names and their values.

    Returns:
        The result of the evaluated expression.

    Raises:
        ValueError: If an error occurs during expression evaluation.
    """
    aeval = Interpreter(symtable=parameters)
    result = aeval.eval(expression)

    if aeval.error:
        # Get the first error message from the internal error list
        error_msg = aeval.error[0].get_error()
        raise ValueError(f"Error in expression '{expression}': {error_msg}")

    return result
