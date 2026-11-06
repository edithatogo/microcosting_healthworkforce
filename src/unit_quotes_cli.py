# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Price explicit snapshot or dated-event quantities against a unit-quote release."""

import argparse
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Annotated, Literal, Self
lazy from datetime import date

from pydantic import Field, TypeAdapter, model_validator

from src.unit_quotes import (
    QuoteModel,
    QuoteQuantity,
    UnitQuoteRelease,
    UnitQuoteResult,
    price_units,
)


class QuoteSnapshotRequest(QuoteModel):
    """An explicit common valuation date and nonempty unit-matched quantities."""

    mode: Literal["snapshot"]
    as_of: date
    quantities: tuple[QuoteQuantity, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def common_date(self) -> Self:
        """Snapshot quantities must all use the requested valuation date."""
        if any(q.valued_on != self.as_of for q in self.quantities):
            msg = "Every snapshot quantity must use the selected as_of date"
            raise ValueError(msg)
        return self


class QuoteEventsRequest(QuoteModel):
    """Already allocated dated quantities, with no inferred duration or split."""

    mode: Literal["events"]
    quantities: tuple[QuoteQuantity, ...] = Field(min_length=1)


type QuoteRequest = Annotated[
    QuoteSnapshotRequest | QuoteEventsRequest,
    Field(discriminator="mode"),
]


@dataclass(frozen=True)
class UnitQuoteRun:
    """Explicit mode/date and exact request-byte hash beside the shared ledger."""

    schema_version: Literal[1]
    mode: Literal["snapshot", "events"]
    as_of: date | None
    request_sha256: str
    result: UnitQuoteResult


def main(argv: list[str] | None = None) -> int:
    """Validate explicit mode/units, reuse price_units and create one new output."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    release_bytes = args.release.read_bytes()
    request_bytes = args.request.read_bytes()
    try:
        release = UnitQuoteRelease.model_validate_json(release_bytes)
        request = TypeAdapter(QuoteRequest).validate_json(request_bytes)
        result = price_units(release, request.quantities)
    except ValueError as error:
        parser.error(str(error))
    run = UnitQuoteRun(
        1,
        request.mode,
        request.as_of if isinstance(request, QuoteSnapshotRequest) else None,
        sha256(request_bytes).hexdigest(),
        result,
    )
    output_bytes = TypeAdapter(UnitQuoteRun).dump_json(run, indent=2) + b"\n"
    with args.output.open("xb") as output:
        output.write(output_bytes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
