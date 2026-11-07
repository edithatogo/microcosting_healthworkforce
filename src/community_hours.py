# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Replay the reviewed Tasmanian rural-medical community-hours schedule."""

from fractions import Fraction

from src.unit_quotes import (
    QuoteQuantity,
    UnitQuoteRelease,
    UnitQuoteResult,
    price_units,
)

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


def tas_rural_community_hours(
    population: int,
    *,
    supports_volunteer_ambulance: bool,
) -> int:
    """Return the community pool using the reviewed Schedule 3 support status."""
    if type(supports_volunteer_ambulance) is not bool:
        msg = "Volunteer ambulance support must be explicitly confirmed or ruled out"
        raise ValueError(msg)
    base = tas_rural_base_community_hours(population)
    return base + (2 if supports_volunteer_ambulance else 0)


def price_tas_rural_community_hours(
    release: UnitQuoteRelease,
    population: int,
    shares: tuple[QuoteQuantity, ...],
    *,
    supports_volunteer_ambulance: bool,
) -> UnitQuoteResult:
    """Price one fortnight's reviewed community allocation at hourly rates.

    Each input quantity is a participant's negotiated fraction. Use one
    valuation date and a distinct quantity identity for each participant.
    """
    hours = tas_rural_community_hours(
        population,
        supports_volunteer_ambulance=supports_volunteer_ambulance,
    )
    shares = tuple(QuoteQuantity.model_validate(dict(share)) for share in shares)
    if (
        len({share.valued_on for share in shares}) != 1
        or any(share.unit != "hour" or not share.basis.strip() for share in shares)
        or sum((Fraction(share.quantity) for share in shares), Fraction(0)) != 1
    ):
        msg = "Community hours require hourly quotes and full shares at one date"
        raise ValueError(msg)
    quantities = tuple(
        share.model_copy(update={"quantity": Fraction(share.quantity) * hours})
        for share in shares
    )
    return price_units(release, quantities)
