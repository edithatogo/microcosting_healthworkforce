# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Run one explicit versioned condition activity calculation from JSON files."""

import argparse
from pathlib import Path

from src.conditions import ConditionRelease, cost_condition_activity
from src.costing import Activity


def main(argv: list[str] | None = None) -> int:
    """Validate both inputs, then create a new output without overwriting files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--activity", type=Path, required=True)
    parser.add_argument("--timezone", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    release = ConditionRelease.model_validate_json(args.release.read_bytes())
    activity = Activity.model_validate_json(args.activity.read_bytes())
    result = cost_condition_activity(release, activity, args.timezone)
    with args.output.open("x", encoding="utf-8") as output:
        output.write(result.model_dump_json())
        output.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
