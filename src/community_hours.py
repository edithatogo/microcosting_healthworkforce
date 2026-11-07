# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Replay the reviewed Tasmanian rural-medical community-hours schedule."""

_LOWER_BREAKPOINT = 5_000
_UPPER_BREAKPOINT = 10_000


def tas_rural_base_community_hours(population: int) -> int:
    """Return base hours per community per fortnight for the retained edition.

    The retained 2025 agreement schedule (PDF pages 16-18) leaves exact breakpoints
    unassigned. The caller supplies the reviewed community population and
    establishes applicability, participation and any separate increment.
    """
    if type(population) is not int or population < 0:
        msg = "Community population must be a nonnegative integer"
        raise ValueError(msg)
    if population in (_LOWER_BREAKPOINT, _UPPER_BREAKPOINT):
        msg = "Community population is at an uncovered schedule breakpoint"
        raise ValueError(msg)
    if population < _LOWER_BREAKPOINT:
        return 2
    if population < _UPPER_BREAKPOINT:
        return 3
    return 4
