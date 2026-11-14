# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Exact recall quantities with travel caps, rounding and minima kept separate."""

from dataclasses import dataclass
from fractions import Fraction
from typing import Literal
lazy from datetime import timedelta


@dataclass(frozen=True)
class RecallQuantityPolicy:
    """An explicitly selected quantity convention, without inferred entitlement."""

    policy_id: str
    travel_cap_each_way: timedelta
    rounding_quantum: timedelta
    rounding_ties: Literal["half_up", "half_even"]
    minimum: timedelta
    method: Literal["cap_travel_sum_round_then_minimum_v1"]


@dataclass(frozen=True)
class RecallQuantity:
    """Retain original, eligible, rounded and guaranteed durations independently."""

    event_id: str
    policy: RecallQuantityPolicy
    worked_microseconds: int
    outbound_travel_microseconds: int
    return_travel_microseconds: int
    eligible_outbound_microseconds: int
    eligible_return_microseconds: int
    eligible_microseconds: int
    rounded_microseconds: int
    payable_microseconds: int

    @property
    def payable_hours(self) -> Fraction:
        """Return exact resource hours without decimal-context rounding."""
        return Fraction(self.payable_microseconds, 3600000000)

    @property
    def rounding_adjustment_microseconds(self) -> int:
        """Allow a negative rounding adjustment while retaining actual evidence."""
        return self.rounded_microseconds - self.eligible_microseconds

    @property
    def minimum_increment_microseconds(self) -> int:
        """Return the guarantee increment after the selected rounding convention."""
        return self.payable_microseconds - self.rounded_microseconds


def _micros(value: timedelta) -> int:
    return (value.days * 86400 + value.seconds) * 1000000 + value.microseconds


def quantify_recall(
    event_id: str,
    worked: timedelta,
    outbound_travel: timedelta,
    return_travel: timedelta,
    policy: RecallQuantityPolicy,
) -> RecallQuantity:
    """Cap each actual journey, sum with work, round, then apply one minimum.

    This is one independently eligible recall quantity, not a repeat-recall
    eligibility decision. The caller must qualify the convention, scope and
    source separately. No paid quantity is converted into worked overtime time
    or an invented time interval for effective-dated pricing.
    """
    if not event_id.strip() or not policy.policy_id.strip():
        msg = "Recall event and policy identities must be nonblank"
        raise ValueError(msg)
    if policy.method != "cap_travel_sum_round_then_minimum_v1":
        msg = "Unsupported recall quantity method"
        raise ValueError(msg)
    if policy.rounding_ties not in ("half_up", "half_even"):
        msg = "Select an explicit rounding tie convention"
        raise ValueError(msg)
    work, outbound, inbound, cap, quantum, minimum = (
        _micros(item)
        for item in (
            worked,
            outbound_travel,
            return_travel,
            policy.travel_cap_each_way,
            policy.rounding_quantum,
            policy.minimum,
        )
    )
    if work <= 0 or quantum <= 0 or min(outbound, inbound, cap, minimum) < 0:
        msg = "Require positive work/quantum and nonnegative travel, cap and minimum"
        raise ValueError(msg)
    eligible_outbound, eligible_return = min(outbound, cap), min(inbound, cap)
    eligible = work + eligible_outbound + eligible_return
    whole, remainder = divmod(eligible, quantum)
    if remainder * 2 > quantum or (
        remainder * 2 == quantum
        and (policy.rounding_ties == "half_up" or whole % 2 == 1)
    ):
        whole += 1
    rounded = whole * quantum
    return RecallQuantity(
        event_id,
        policy,
        work,
        outbound,
        inbound,
        eligible_outbound,
        eligible_return,
        eligible,
        rounded,
        max(rounded, minimum),
    )
