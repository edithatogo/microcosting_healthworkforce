# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Price explicitly planned recall windows through the effective-dated ledger."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal
lazy from datetime import timedelta

from src.costing import Activity, CostRelease, CostResult, cost_dynamic
from src.recall_windows import RecallEvent, RecallWindow, plan_recall_windows


@dataclass(frozen=True)
class RecallCost:
    """Keep actual-event planning and paid-window pricing evidence together."""

    method_id: str
    windows: tuple[RecallWindow, ...]
    ledger: CostResult


def cost_recall_windows(
    release: CostRelease,
    resource_id: str,
    events: tuple[RecallEvent, ...],
    minimum: timedelta,
    grouping_method: Literal["anchored_first_recall_v1"],
) -> RecallCost:
    """Price guaranteed intervals with caller-qualified precomputed rates.

    Rate composition, eligibility and the selected grouping convention must be
    established by the caller. Worked event time is not used as overtime history;
    guarantee time and actual work remain separate in the returned evidence.
    """
    windows = plan_recall_windows(events, minimum, grouping_method)
    activities = tuple(
        Activity(
            activity_id="recall-window:" + window.events[0].event_id,
            resource_id=resource_id,
            allocation_id=window.allocation_id,
            starts_at=window.starts_at,
            ends_at=window.paid_ends_at,
            resources=Decimal(1),
        )
        for window in windows
    )
    return RecallCost(
        "anchored_window_flat_rate_v1",
        windows,
        cost_dynamic(release, activities),
    )
