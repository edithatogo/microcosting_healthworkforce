# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Public-source transport and adversarial quotation-artifact contracts."""

import json
from copy import deepcopy
from datetime import date
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest
from pydantic import TypeAdapter

from microcosting_healthworkforce.dapane_adapter import (
    DapaneQuoteBinding,
    build_dapane_request,
    evaluate_dapane,
    export_dapane_quotes,
    load_dapane_quotes_json,
    strict_json_object,
)
from microcosting_healthworkforce.unit_quotes import (
    QuoteQuantity,
    UnitQuoteRelease,
    price_units,
)
from tests.checks import assert_that

lazy from microcosting_healthworkforce.dapane_adapter import JsonObject

_EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "dapane"
_PIN = "9cd5e8bb48b29186b7fd4ea911f914c0e0dbf4f3fc188a1f6728cbe65947ec60"


def public_release() -> UnitQuoteRelease:
    """Load the one explicitly bounded public hourly-reference quotation."""
    return UnitQuoteRelease.model_validate_json(
        (_EXAMPLES / "qld-hp3p1-release.json").read_bytes(),
    )


def public_bindings() -> tuple[DapaneQuoteBinding, ...]:
    """Load unchanged hourly value and explicit minute denominator bindings."""
    return TypeAdapter(tuple[DapaneQuoteBinding, ...]).validate_json(
        (_EXAMPLES / "qld-hp3p1-bindings.json").read_bytes(),
    )


def artifact() -> JsonObject:
    """Regenerate the independent artifact fixture from provider models."""
    return export_dapane_quotes(public_release(), public_bindings())


def exposure() -> QuoteQuantity:
    """Supply a synthetic one-third minute, never a binary float."""
    return QuoteQuantity(
        quantity_id="synthetic-exposure",
        quote_id="qld-hp3p1-minute-20260901",
        unit="minute",
        quantity=Fraction(1, 3),
        valued_on=date(2026, 11, 15),
        quantity_kind="analyst_assumption",
        basis="Synthetic exact transport case, not observed staffing",
    )


def _repin(value: JsonObject) -> str:
    """Recompute an adversarial envelope pin without trusting its semantics."""
    value.pop("artifact_sha256", None)
    encoded = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    digest = sha256(encoded).hexdigest()
    value["artifact_sha256"] = digest
    return digest


def test_public_source_round_trip_and_exact_minute_denominator() -> None:
    """One published rate is copied unchanged into hour and minute quotes."""
    result = artifact()
    checked = load_dapane_quotes_json(json.dumps(result), expected_sha256=_PIN)
    stored = strict_json_object(
        (_EXAMPLES / "qld-hp3p1-quotes.json").read_text(encoding="utf-8"),
    )
    assert_that(checked == stored == result)
    assert_that(result["artifact_sha256"] == _PIN)
    quotes = cast("list[JsonObject]", result["quotes"])
    assert_that([q["amount"] for q in quotes] == ["46.0658", "46.0658"])
    assert_that([q["per_quantity"] for q in quotes] == ["1", "60"])
    assert_that(all(q["components"] == ["base_salary"] for q in quotes))
    assert_that(all(q["basis"] == "financial_cost" for q in quotes))


def test_snapshot_does_not_alias_mutable_export_or_source_models() -> None:
    """Changing a returned artifact neither mutates inputs nor passes old pins."""
    release = public_release()
    original = release.model_dump_json()
    first = export_dapane_quotes(release, public_bindings())
    second = export_dapane_quotes(release, public_bindings())
    quotes = cast("list[JsonObject]", first["quotes"])
    quotes[0]["amount"] = "1.00"
    assert_that(release.model_dump_json() == original)
    assert_that(second == artifact())
    with pytest.raises(ValueError, match="content digest"):
        load_dapane_quotes_json(json.dumps(first), expected_sha256=_PIN)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("amount", "46.06"),
        ("known_from", "2026-01-01"),
        ("valid_to", "2099-01-01"),
        ("components", ["salary_synonym"]),
        ("source", {"id": "substituted"}),
    ],
)
def test_self_consistent_hash_cannot_substitute_exported_quote(
    field: str,
    value: str | list[str] | dict[str, str],
) -> None:
    """A newly hashed alteration still has to agree with its source snapshot."""
    changed = deepcopy(artifact())
    quotes = cast("list[dict[str, object]]", changed["quotes"])
    quotes[0][field] = value
    pin = _repin(changed)
    with pytest.raises(ValueError, match="differs"):
        load_dapane_quotes_json(json.dumps(changed), expected_sha256=pin)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", "workforce-dapane-quotes/99"),
        ("release_sha256", "0" * 64),
        ("release_id", "substitute"),
        ("as_known_on", "2020-01-01"),
        ("provider", {"name": "different"}),
        ("extra", "unrecognized"),
    ],
)
def test_hash_does_not_bypass_provider_or_release_identity(
    field: str,
    value: str | dict[str, str],
) -> None:
    """Provider, snapshot hash, method and release identity remain coupled."""
    changed = deepcopy(artifact())
    changed[field] = cast("JsonObject | str", value)
    pin = _repin(changed)
    with pytest.raises(ValueError, match="differs"):
        load_dapane_quotes_json(json.dumps(changed), expected_sha256=pin)


@pytest.mark.parametrize(
    "text",
    [
        '{"a": 1, "a": 2}',
        '{"outer": {"duplicate": 1, "duplicate": 2}}',
        '{"amount": 1.25}',
        '{"amount": NaN}',
        '{"amount": Infinity}',
        '{"amount": -Infinity}',
        '{"amount": 1e999}',
    ],
)
def test_json_rejects_duplicates_and_inexact_numeric_literals(text: str) -> None:
    """Transport must not hide a substituted key or coerce floating amounts."""
    with pytest.raises(ValueError, match="Duplicate|floating|nonfinite"):
        strict_json_object(text)


def test_json_rejects_oversize_nesting_and_invalid_top_level() -> None:
    """Bounded transport rejects resource exhaustion before model admission."""
    with pytest.raises(ValueError, match="byte limit"):
        strict_json_object('{"payload":"' + "x" * 2_000_000 + '"}')
    with pytest.raises(ValueError, match="nesting"):
        strict_json_object('{"value":' + "[" * 70 + "0" + "]" * 70 + "}")
    with pytest.raises(ValueError, match="object"):
        strict_json_object("[]")


@pytest.mark.parametrize("pin", ["", "A" * 64, "0" * 63, "0" * 64])
def test_external_pin_is_required(pin: str) -> None:
    """An artifact cannot authenticate itself by carrying its own digest."""
    with pytest.raises(ValueError, match="pin|SHA-256"):
        load_dapane_quotes_json(json.dumps(artifact()), expected_sha256=pin)


def test_export_revalidates_bypassed_provider_models() -> None:
    """Unchecked model copies cannot promote unaccepted or mismatched quotes."""
    release = public_release()
    changed_quote = release.quotes[0].model_copy(update={"status": "candidate"})
    changed = release.model_copy(update={"quotes": (changed_quote,)})
    with pytest.raises(ValueError, match="accepted"):
        export_dapane_quotes(changed, public_bindings())
    other = release.model_copy(update={"employer": "Unreviewed employer"})
    with pytest.raises(ValueError, match="scope"):
        export_dapane_quotes(other, public_bindings())


@pytest.mark.parametrize(
    "updates",
    [
        {"components": ("oncost",)},
        {"components": ("base_salary", "oncost")},
        {"components": ("base_salary", "base_salary")},
        {"per_quantity": "1"},
        {"unit": "second"},
        {"provider_quote_id": "absent"},
        {"price_year": True},
    ],
)
def test_binding_cannot_relabel_components_or_infer_denominators(
    updates: dict[str, object],
) -> None:
    """The source's component and explicit supported unit relation are binding."""
    binding = public_bindings()[1].model_copy(update=updates)
    with pytest.raises(ValueError, match="component|unit|absent|integer"):
        export_dapane_quotes(public_release(), (binding,))


def test_duplicate_or_empty_binding_ids_are_rejected() -> None:
    """Ambiguous exported identities cannot select a quotation silently."""
    binding = public_bindings()[0]
    for bindings in ((), (binding, binding)):
        with pytest.raises(ValueError, match="unique"):
            export_dapane_quotes(public_release(), bindings)


def test_transport_exact_exposure_and_knowledge_boundary() -> None:
    """Exposure and source amount are transported without pricing in Python."""
    text = json.dumps(artifact())
    request = build_dapane_request(
        text,
        (exposure(),),
        expected_sha256=_PIN,
        run_id="transport",
        knowledge_cutoff=date(2026, 11, 15),
    )
    usage = cast("list[JsonObject]", request["usage"])
    assert_that(usage[0]["quantity"] == {"numerator": "1", "denominator": "3"})
    assert_that(usage[0]["unit"] == "minute")
    with pytest.raises(ValueError, match="precedes"):
        build_dapane_request(
            text,
            (exposure(),),
            expected_sha256=_PIN,
            run_id="early",
            knowledge_cutoff=date(2026, 11, 14),
        )
    with pytest.raises(ValueError, match="same unit"):
        build_dapane_request(
            text,
            (exposure().model_copy(update={"unit": "hour"}),),
            expected_sha256=_PIN,
            run_id="wrong-unit",
            knowledge_cutoff=date(2026, 11, 15),
        )


def test_legacy_exact_value_and_digest_contract_remain_distinct() -> None:
    """The old engine remains an explicit comparator with its original pin."""
    release = public_release()
    quantity = exposure().model_copy(
        update={
            "quote_id": release.quotes[0].quote_id,
            "unit": "hour",
            "quantity": Decimal("1"),
        },
    )
    original = price_units(release, (quantity,))
    assert_that(original.total == Fraction(230329, 5000))
    assert_that(
        original.release_sha256
        == sha256(release.model_dump_json().encode()).hexdigest(),
    )
    assert_that(original.release_sha256 != artifact()["release_sha256"])


def test_optional_consumer_passes_the_request_to_installed_dapane() -> None:
    """The consumer has no separate Python valuation fallback."""

    class KernelSpy:
        """Record the public boundary; numerical qualification is separate."""

        request: JsonObject | None = None

        def evaluate(self, request: JsonObject) -> JsonObject:
            """Return a sentinel without pretending to calculate a result."""
            self.request = request
            return {"boundary": "native"}

    kernel = KernelSpy()
    with patch(
        "microcosting_healthworkforce.dapane_adapter.import_module",
        return_value=kernel,
    ):
        result = evaluate_dapane(
            json.dumps(artifact()),
            (exposure(),),
            expected_sha256=_PIN,
            run_id="boundary",
            knowledge_cutoff=date(2026, 11, 15),
        )
    assert_that(result == {"boundary": "native"})
    assert_that(kernel.request is not None)


@pytest.mark.parametrize(
    "amount",
    ["1E+1000000000", "1E-1000000000", "1E+96", "1E-37", "-0"],
)
def test_decimal_expansion_is_bounded_before_fixed_point_encoding(amount: str) -> None:
    """Compact exponent inputs cannot allocate huge strings or lose precision."""
    release = public_release()
    quote = release.quotes[0].model_copy(update={"amount": Decimal(amount)})
    candidate = release.model_copy(update={"quotes": (quote,)})
    with pytest.raises(ValueError, match="digits|scale|unsigned"):
        export_dapane_quotes(candidate, public_bindings())


def test_modest_exponent_is_exact_transport_without_numeric_revaluation() -> None:
    """A small synthetic exponent preserves the amount's exact decimal value."""
    release = public_release()
    quote = release.quotes[0].model_copy(update={"amount": Decimal("1E+2")})
    candidate = release.model_copy(update={"quotes": (quote,)})
    exported = export_dapane_quotes(candidate, public_bindings())
    quotes = cast("list[JsonObject]", exported["quotes"])
    snapshot = cast("JsonObject", exported["release_snapshot"])
    original_quotes = cast("list[JsonObject]", snapshot["quotes"])
    assert_that(original_quotes[0]["amount"] == "1E+2")
    assert_that([item["amount"] for item in quotes] == ["100", "100"])
    pin = cast("str", exported["artifact_sha256"])
    assert_that(
        load_dapane_quotes_json(json.dumps(exported), expected_sha256=pin) == exported,
    )


@pytest.mark.parametrize(
    "value",
    [Decimal("1E+1000000000"), Decimal("1E-37"), Fraction(10**96), Fraction(1, 10**96)],
)
def test_quantity_transport_has_the_same_precision_bounds(
    value: Decimal | Fraction,
) -> None:
    """Exact quantities also fail before oversized decimal or rational output."""
    quantity = exposure().model_copy(update={"quantity": value})
    with pytest.raises(ValueError, match="digits|scale|precision"):
        build_dapane_request(
            json.dumps(artifact()),
            (quantity,),
            expected_sha256=_PIN,
            run_id="overlarge",
            knowledge_cutoff=date(2026, 11, 15),
        )


def test_source_kind_is_not_implicitly_promoted() -> None:
    """Only the explicit public-reference profile or labelled synthetic input exports."""
    release = public_release()
    original = release.sources.records[0]
    unqualified_source = original.model_copy(update={"kind": "unqualified_source"})
    unqualified_registry = release.sources.model_copy(
        update={"records": (unqualified_source,)},
    )
    with pytest.raises(ValueError, match="source kind"):
        export_dapane_quotes(
            release.model_copy(update={"sources": unqualified_registry}),
            public_bindings(),
        )
    synthetic_source = original.model_copy(update={"kind": "synthetic"})
    synthetic_registry = release.sources.model_copy(
        update={"records": (synthetic_source,)},
    )
    synthetic = export_dapane_quotes(
        release.model_copy(update={"sources": synthetic_registry}),
        public_bindings(),
    )
    quotes = cast("list[JsonObject]", synthetic["quotes"])
    source = cast("JsonObject", quotes[0]["source"])
    assert_that(source["evidence"] == "synthetic")
    assert_that(source["validation"] == "unvalidated")
