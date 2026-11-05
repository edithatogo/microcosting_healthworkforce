# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
# Typed subset of asteval used by the formula parser.
from collections.abc import Mapping

class ExceptionHolder:
    def get_error(self) -> tuple[str, str]: ...

class Interpreter:
    error: list[ExceptionHolder]
    def __init__(self, symtable: Mapping[str, object]) -> None: ...
    def eval(self, expr: str) -> object: ...
