# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Validate scalars at the Polars-to-numeric boundary."""

from typing import cast


def numeric(value: object) -> float:
    """Return a numeric summary or reject a nonnumeric scalar."""
    if not isinstance(value, (int, float)):
        message = "Expected a numeric summary from a nonempty numeric column"
        raise TypeError(message)
    return float(value)


def row_filter(value: object) -> dict[str, str | int | float | bool]:
    """Validate equality filters supplied by a scenario JSON record."""
    if value is None:
        return {}
    if not isinstance(value, dict):
        message = "Row filter must be a mapping"
        raise TypeError(message)
    result: dict[str, str | int | float | bool] = {}
    for key, item in cast("dict[object, object]", value).items():
        if not isinstance(key, str) or not isinstance(item, (str, int, float, bool)):
            message = "Row filter keys and values must be scalar"
            raise TypeError(message)
        result[key] = item
    return result
