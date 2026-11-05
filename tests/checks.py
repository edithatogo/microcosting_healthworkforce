# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Always-on assertion predicates retained from the original pytest checks."""


def assert_that(condition: object, message: object = None) -> None:
    """Fail on the same predicate even when Python runs with optimisation."""
    if not condition:
        raise AssertionError(message)
