# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Exercise explicit static/event unit pricing through the shared calculator."""

import json
from datetime import date
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
lazy from pathlib import Path

import pytest
from pydantic import TypeAdapter

from src.unit_quotes import QuoteQuantity, UnitQuoteRelease, price_units
from src.unit_quotes_cli import UnitQuoteRun, main
from tests.checks import assert_that
from tests.test_unit_quotes import quantity, quote, release

ARGUMENT_ERROR = 2


def payload(
    quantities: tuple[QuoteQuantity, ...],
    *,
    mode: str = "snapshot",
    as_of: str | None = "2026-02-01",
) -> str:
    """Serialize exact quantity values with an explicit test mode/date."""
    values: dict[str, object] = {
        "mode": mode,
        "quantities": [q.model_dump(mode="json") for q in quantities],
    }
    if as_of is not None:
        values["as_of"] = as_of
    return json.dumps(values)


def inputs(
    tmp_path: Path,
    request: str,
    rates: UnitQuoteRelease | None = None,
) -> tuple[list[str], Path]:
    """Write isolated synthetic inputs and return the real CLI argument contract."""
    release_path = tmp_path / "release.json"
    request_path = tmp_path / "request.json"
    output = tmp_path / "result.json"
    release_path.write_text((rates or release()).model_dump_json(), encoding="utf-8")
    request_path.write_text(request, encoding="utf-8")
    return [
        "--release",
        str(release_path),
        "--request",
        str(request_path),
        "--output",
        str(output),
    ], output


def test_snapshot_cli_prices_the_explicit_unit(tmp_path: Path) -> None:
    """The CLI reaches the library and preserves exact lineage and request bytes."""
    quantities = (quantity(),)
    request = payload(quantities)
    args, output = inputs(tmp_path, request)
    assert_that(main(args) == 0)
    run = TypeAdapter(UnitQuoteRun).validate_json(output.read_bytes())
    assert_that(run.schema_version == 1 and run.mode == "snapshot")
    assert_that(run.as_of == date(2026, 2, 1))
    assert_that(run.result == price_units(release(), quantities))
    assert_that(run.result.total == Fraction(10001, 100))
    assert_that(run.request_sha256 == sha256(request.encode()).hexdigest())
    assert_that(run.result.rows[0].quote.source_sha256 == "a" * 64)
    assert_that(output.read_bytes().endswith(b"\n"))


def test_events_select_each_explicit_version_at_the_change(tmp_path: Path) -> None:
    """Dated quantities retain original units, quote choices and signed-free costs."""
    rates = release(
        quote(ends_on=date(2026, 7, 1)),
        quote(
            quote_id="period-2",
            starts_on=date(2026, 7, 1),
            amount=Decimal("110.01"),
        ),
        quote(
            quote_id="annual",
            component="registration",
            unit="annum",
            amount=Decimal(2700),
        ),
    )
    quantities = (
        quantity(valued_on=date(2026, 6, 30)),
        quantity(
            quantity_id="event-2",
            quote_id="period-2",
            valued_on=date(2026, 7, 1),
        ),
        quantity(quantity_id="annual", quote_id="annual", unit="annum"),
    )
    args, output = inputs(
        tmp_path,
        payload(quantities, mode="events", as_of=None),
        rates,
    )
    assert_that(main(args) == 0)
    run = TypeAdapter(UnitQuoteRun).validate_json(output.read_bytes())
    assert_that(run.mode == "events" and run.as_of is None)
    assert_that(run.result == price_units(rates, quantities))
    assert_that(run.result.total == Fraction(145501, 50))
    assert_that(
        [r.quantity.unit for r in run.result.rows]
        == ["fortnight", "fortnight", "annum"],
    )


def test_fraction_json_survives_low_decimal_precision(tmp_path: Path) -> None:
    """The file interface cannot round an exact one-third quantity into a decimal."""
    args, output = inputs(tmp_path, payload((quantity(quantity=Fraction(1, 3)),)))
    with localcontext() as context:
        context.prec = 3
        assert_that(main(args) == 0)
    run = TypeAdapter(UnitQuoteRun).validate_json(output.read_bytes())
    assert_that(run.result.total == Fraction(10001, 300))
    assert_that(run.result.rows[0].quantity.quantity == Fraction(1, 3))


def test_known_zero_is_priced_but_empty_request_is_rejected(tmp_path: Path) -> None:
    """A real declared zero has a ledger row and is distinct from missing input."""
    args, output = inputs(tmp_path, payload((quantity(quantity=Decimal(0)),)))
    assert_that(main(args) == 0)
    run = TypeAdapter(UnitQuoteRun).validate_json(output.read_bytes())
    assert_that(run.result.total == 0 and len(run.result.rows) == 1)


@pytest.mark.parametrize(
    "request_text",
    [
        "not json",
        '{"quantities":[]}',
        '{"mode":"other","quantities":[]}',
        '{"mode":"snapshot","quantities":[]}',
        '{"mode":"snapshot","as_of":"2026-02-01","quantities":[]}',
        '{"mode":"events","quantities":[]}',
        payload((quantity(),), mode="events"),
        payload((quantity(),), as_of="2026-02-02"),
        payload((quantity(unit="annum"),)),
        payload((quantity(quote_id="missing"),)),
        payload((quantity(valued_on=date(2027, 1, 1)),), as_of="2027-01-01"),
        payload((quantity(), quantity())),
    ],
)
def test_invalid_request_creates_no_result(tmp_path: Path, request_text: str) -> None:
    """Mode, dates, units and missing/duplicate inputs fail before output creation."""
    args, output = inputs(tmp_path, request_text)
    with pytest.raises(SystemExit) as error:
        main(args)
    assert_that(error.value.code == ARGUMENT_ERROR)
    assert_that(not output.exists())


def test_unresolved_release_cannot_be_used_by_cli(tmp_path: Path) -> None:
    """Structural input mode does not bypass source applicability review."""
    args, output = inputs(tmp_path, payload((quantity(),)))
    release_path = tmp_path / "release.json"
    release_path.write_text(
        release_path.read_text(encoding="utf-8").replace(
            '"applicability":"verified"',
            '"applicability":"unresolved"',
        ),
        encoding="utf-8",
    )
    with pytest.raises(SystemExit, match="2"):
        main(args)
    assert_that(not output.exists())


@pytest.mark.parametrize("existing", ["result.json", "release.json", "request.json"])
def test_existing_output_or_input_alias_is_never_overwritten(
    tmp_path: Path,
    existing: str,
) -> None:
    """Exclusive output creation preserves earlier results and both input files."""
    args, _ = inputs(tmp_path, payload((quantity(),)))
    output = tmp_path / existing
    if not output.exists():
        output.write_bytes(b"earlier result\n")
    before = output.read_bytes()
    args[-1] = str(output)
    with pytest.raises(FileExistsError):
        main(args)
    assert_that(output.read_bytes() == before)


def test_cli_requires_all_paths_and_documents_both_modes() -> None:
    """Missing paths fail explicitly while help remains a side-effect-free command."""
    with pytest.raises(SystemExit) as missing:
        main([])
    assert_that(missing.value.code == ARGUMENT_ERROR)
    with pytest.raises(SystemExit) as help_result:
        main(["--help"])
    assert_that(help_result.value.code == 0)


@pytest.mark.parametrize("mode", ["snapshot", "events"])
def test_negative_allowance_scenario_cannot_enter_quote_ledger(
    tmp_path: Path,
    mode: str,
) -> None:
    """A negative legacy perturbation cannot become a successor unit price."""
    rates = release(
        quote(component="professional_development_allowance", amount=Decimal(0)),
    )
    args, output = inputs(
        tmp_path,
        payload(
            (quantity(),),
            mode=mode,
            as_of="2026-02-01" if mode == "snapshot" else None,
        ),
        rates,
    )
    release_path = tmp_path / "release.json"
    invalid = rates.model_dump(mode="json")
    invalid["quotes"][0]["amount"] = "-500"
    release_path.write_text(json.dumps(invalid), encoding="utf-8")
    with pytest.raises(SystemExit) as error:
        main(args)
    assert_that(error.value.code == ARGUMENT_ERROR)
    assert_that(not output.exists())
