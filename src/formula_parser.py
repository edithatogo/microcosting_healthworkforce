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
        NameError: If the expression contains a variable not in the parameters.
        SyntaxError: If the expression is not valid Python syntax.
    """
    aeval = Interpreter(symtable=parameters)
    try:
        return aeval.eval(expression)
    except NameError as e:
        raise NameError(f"A parameter in the expression is not defined: {e}")
    except SyntaxError:
        raise SyntaxError(f"Invalid syntax in expression: {expression}")
    except Exception as e:
        raise type(e)(f"An error occurred during expression evaluation: {e}")
