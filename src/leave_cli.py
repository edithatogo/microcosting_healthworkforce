# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Price a reviewed paid-leave schedule against a versioned quote release."""

import argparse
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from pydantic import TypeAdapter

from src.historical_hours import (
    HistoricalHours,
    HoursHistoryRequest,
    NormalHoursRule,
    select_normal_hours,
)
from src.leave_pricing import (
    LeaveLoadingMoneyCap,
    LeavePriceSelection,
    PricedLeave,
    price_paid_leave,
)
from src.paid_leave import PaidLeavePolicy, PaidLeaveRequest, build_paid_leave
from src.unit_quotes import QuoteModel, UnitQuoteRelease


class LeaveCostRequest(QuoteModel):
    """Original schedule, hours and price declarations for one costing run."""

    policy: PaidLeavePolicy
    leave: PaidLeaveRequest
    hours_rule: NormalHoursRule
    hours_request: HoursHistoryRequest
    hours_history: tuple[HistoricalHours, ...]
    choices: tuple[LeavePriceSelection, ...]
    loading_caps: tuple[LeaveLoadingMoneyCap, ...] = ()


@dataclass(frozen=True)
class LeaveCostRun:
    """Source byte digests and the shared paid-leave ledger."""

    schema_version: int
    release_sha256: str
    request_sha256: str
    result: PricedLeave


def main(argv: list[str] | None = None) -> int:
    """Validate input files and create a new ledger without overwriting."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    release_bytes = args.release.read_bytes()
    request_bytes = args.request.read_bytes()
    try:
        release = UnitQuoteRelease.model_validate_json(release_bytes)
        request = LeaveCostRequest.model_validate_json(request_bytes)
        result = price_paid_leave(
            release,
            select_normal_hours(
                request.hours_rule,
                request.hours_request,
                request.hours_history,
            ),
            build_paid_leave(request.policy, request.leave),
            request.choices,
            loading_cap=request.loading_caps,
        )
    except ValueError as error:
        parser.error(str(error))
    run = LeaveCostRun(
        1,
        sha256(release_bytes).hexdigest(),
        sha256(request_bytes).hexdigest(),
        result,
    )
    with args.output.open("xb") as output:
        output.write(TypeAdapter(LeaveCostRun).dump_json(run, indent=2) + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
