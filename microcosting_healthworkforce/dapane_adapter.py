# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Exact public quotation transport and an optional Dapane numerical consumer.

Domain admission remains in UnitQuoteRelease. This module neither calculates
prices nor applies employment rules. It copies a selected source amount and
encodes an explicit hour-to-minute denominator for the shared Rust evaluator.
"""

import json
import re
from datetime import date
from fractions import Fraction
from hashlib import sha256
from importlib import import_module
from typing import Literal, Protocol, Self, cast
lazy from decimal import Decimal
lazy from typing import NoReturn

from pydantic import Field, TypeAdapter, model_validator

from microcosting_healthworkforce.unit_quotes import (
    QuoteModel,
    QuoteQuantity,
    UnitQuoteRelease,
)

type JsonValue = bool | int | str | list[JsonValue] | dict[str, JsonValue] | None
type JsonObject = dict[str, JsonValue]

_SCHEMA = "workforce-dapane-quotes/1"
_MAX_BYTES = 2_000_000
_MAX_DEPTH = 64
_MAX_NUMERIC_DIGITS = 96
_MAX_DECIMAL_SCALE = 36
_MAX_NUMERIC_BITS = 320
_DIGEST = re.compile(r"^[a-f0-9]{64}$")


def _reject_number(value: str) -> NoReturn:
    """Reject floats and nonfinite JSON values before decimal model parsing."""
    message = f"JSON floating or nonfinite number is forbidden: {value}"
    raise ValueError(message)


def _unique_object(pairs: list[tuple[str, JsonValue]]) -> JsonObject:
    """Reject duplicate JSON keys instead of accepting last-value-wins input."""
    result: JsonObject = {}
    for key, value in pairs:
        if key in result:
            message = f"Duplicate JSON key: {key}"
            raise ValueError(message)
        result[key] = value
    return result


def _depth(value: JsonValue, depth: int = 0) -> None:
    """Bound transport nesting and reject unsupported host scalar types."""
    if depth > _MAX_DEPTH:
        message = "JSON transport exceeds the nesting limit"
        raise ValueError(message)
    if isinstance(value, dict):
        for item in value.values():
            _depth(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            _depth(item, depth + 1)
    elif value is not None and type(value) not in {str, int, bool}:
        message = "JSON transport requires exact strings, not floating values"
        raise ValueError(message)


def _canonical(value: JsonValue) -> str:
    """Serialize the v1 canonical transport, without numeric interpretation."""
    try:
        _depth(value)
        encoded = json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
        if len(encoded.encode("utf-8")) > _MAX_BYTES:
            message = "JSON transport exceeds the byte limit"
            raise ValueError(message)
    except (RecursionError, UnicodeError) as error:
        message = "Invalid JSON transport nesting or Unicode"
        raise ValueError(message) from error
    return encoded


def _sha256(value: JsonValue) -> str:
    """Hash canonical UTF-8 JSON, distinct from the unchanged legacy pin."""
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


def _object(value: JsonValue) -> JsonObject:
    """Require an object at a structural contract boundary."""
    if not isinstance(value, dict):
        message = "Expected a JSON object"
        raise TypeError(message)
    return value


def _array(value: JsonValue) -> list[JsonValue]:
    """Require an array at a structural contract boundary."""
    if not isinstance(value, list):
        message = "Expected a JSON array"
        raise TypeError(message)
    return value


def _string(value: JsonValue) -> str:
    """Require a string without coercing a numeric or absent identifier."""
    if not isinstance(value, str):
        message = "Expected a JSON string"
        raise TypeError(message)
    return value


def strict_json_object(text: object) -> JsonObject:
    """Read bounded JSON with duplicate-key and binary-float rejection."""
    if not isinstance(text, str):
        message = "JSON input must be text"
        raise TypeError(message)
    try:
        if len(text.encode("utf-8")) > _MAX_BYTES:
            message = "JSON transport exceeds the byte limit"
            raise ValueError(message)
        value = cast(
            "JsonValue",
            json.loads(
                text,
                object_pairs_hook=_unique_object,
                parse_float=_reject_number,
                parse_constant=_reject_number,
            ),
        )
        _depth(value)
    except (RecursionError, UnicodeError) as error:
        message = "Invalid JSON transport nesting or Unicode"
        raise ValueError(message) from error
    return _object(value)


class DapaneQuoteBinding(QuoteModel):
    """Reviewed source-to-resource binding; no inferred worker eligibility."""

    provider_quote_id: str
    quote_id: str
    target: str
    unit: str
    per_quantity: Literal["1", "60"]
    components: tuple[str, ...] = Field(min_length=1)
    component_basis: str
    price_year: int = Field(ge=1, le=9999)

    @model_validator(mode="after")
    def distinct_components(self) -> Self:
        """Require explicit stable, distinct component identities."""
        if len(set(self.components)) != len(self.components) or any(
            not component.strip() or component != component.strip()
            for component in self.components
        ):
            message = "Binding components must be distinct nonblank identifiers"
            raise ValueError(message)
        return self


def _json_model(value: QuoteModel) -> JsonObject:
    """Convert model scalar types through the same strict JSON boundary."""
    return strict_json_object(value.model_dump_json())


def _decimal(value: Decimal) -> str:
    """Bound exact decimal expansion before allocating a fixed-point string."""
    if not value.is_finite() or value.is_signed():
        message = "Dapane transport requires finite unsigned decimal values"
        raise ValueError(message)
    number = value.as_tuple()
    exponent = cast("int", number.exponent)
    scale = max(-exponent, 0)
    digits = max(len(number.digits) + exponent, 1) + scale
    if digits > _MAX_NUMERIC_DIGITS or scale > _MAX_DECIMAL_SCALE:
        message = "Decimal transport exceeds 96 digits or scale 36"
        raise ValueError(message)
    return format(value, "f")


def _unsigned_integer(value: int) -> str:
    """Bound a rational component before decimal string conversion."""
    if value < 0 or value.bit_length() > _MAX_NUMERIC_BITS:
        message = "Rational transport exceeds the unsigned precision limit"
        raise ValueError(message)
    encoded = str(value)
    if len(encoded) > _MAX_NUMERIC_DIGITS:
        message = "Rational transport exceeds 96 digits"
        raise ValueError(message)
    return encoded


def _export_quote(
    release: UnitQuoteRelease,
    binding: DapaneQuoteBinding,
) -> JsonObject:
    """Copy source values; encode minute exposure without dividing the rate."""
    quote = next(
        (item for item in release.quotes if item.quote_id == binding.provider_quote_id),
        None,
    )
    if quote is None:
        message = "Binding names an absent provider quote"
        raise ValueError(message)
    if binding.components != (quote.component,):
        message = "Binding must retain the source quote's single component"
        raise ValueError(message)
    conversion = (quote.unit, binding.unit, binding.per_quantity)
    if not (
        (quote.unit == binding.unit and binding.per_quantity == "1")
        or conversion == ("hour", "minute", "60")
    ):
        message = "Unsupported unit binding; only identity or hour/minute is supported"
        raise ValueError(message)
    source = next(
        item for item in release.sources.records if item.source_id == quote.source_id
    )
    if source.kind not in {"published_wage_reference", "synthetic"}:
        message = "Unsupported public source kind for the bounded adapter"
        raise ValueError(message)
    synthetic = source.kind == "synthetic"
    return {
        "id": binding.quote_id,
        "kind": "resource_use",
        "target": binding.target,
        "unit": binding.unit,
        "amount": _decimal(quote.amount),
        "per_quantity": binding.per_quantity,
        "currency": release.currency,
        "price_year": binding.price_year,
        "basis": "financial_cost",
        "components": list(binding.components),
        "valid_from": quote.starts_on.isoformat(),
        "valid_to": quote.ends_on.isoformat(),
        "known_from": quote.known_from.isoformat(),
        "source": {
            "id": source.source_id,
            "version": release.release_id,
            "evidence": "synthetic" if synthetic else "observed",
            "access": "public",
            "validation": "unvalidated" if synthetic else "source_verified",
            "content_digest": "sha256:" + quote.source_sha256,
            "locator": source.uri,
        },
    }


def export_dapane_quotes(
    release: UnitQuoteRelease,
    bindings: tuple[DapaneQuoteBinding, ...],
) -> JsonObject:
    """Export a revalidated public release and its exact selected quotations.

    The returned dictionary is an independent snapshot. Its digest covers the
    complete release and bindings, while original source hashes remain beside
    the values. A later mutation changes the artifact identity. Source byte
    verification and eligibility remain separate admission responsibilities.
    """
    release = UnitQuoteRelease.model_validate(release.model_dump())
    bindings = tuple(
        DapaneQuoteBinding.model_validate(binding.model_dump()) for binding in bindings
    )
    if not bindings or len({binding.quote_id for binding in bindings}) != len(bindings):
        message = "Bindings require nonempty, unique exported quote identities"
        raise ValueError(message)
    if len({binding.price_year for binding in bindings}) != 1:
        message = "A quotation artifact requires one explicit price year"
        raise ValueError(message)
    snapshot = _json_model(release)
    result: JsonObject = {
        "schema_version": _SCHEMA,
        "provider": {
            "name": "microcosting-healthworkforce",
            "version": "0.0.1",
            "method_id": release.method_id,
        },
        "release_id": release.release_id,
        "as_known_on": release.as_known_on.isoformat(),
        "release_snapshot": snapshot,
        "release_sha256": _sha256(snapshot),
        "bindings": [_json_model(binding) for binding in bindings],
        "quotes": [_export_quote(release, binding) for binding in bindings],
    }
    result["artifact_sha256"] = _sha256(result)
    return result


def load_dapane_quotes_json(text: str, *, expected_sha256: object) -> JsonObject:
    """Verify an independently supplied pin and regenerate every exported quote.

    A self-consistent hash is not source authorization. The expected pin must
    come from the caller's selected release. Rebuilding prevents a substituted
    exported amount, component, date or source from disagreeing with its snapshot.
    """
    if (
        not isinstance(expected_sha256, str)
        or _DIGEST.fullmatch(expected_sha256) is None
    ):
        message = "An explicit lowercase SHA-256 release pin is required"
        raise ValueError(message)
    payload = strict_json_object(text)
    if payload.get("artifact_sha256") != expected_sha256:
        message = "Quotation artifact pin mismatch"
        raise ValueError(message)
    unsigned = {
        key: value for key, value in payload.items() if key != "artifact_sha256"
    }
    if _sha256(unsigned) != expected_sha256:
        message = "Quotation artifact content digest mismatch"
        raise ValueError(message)
    try:
        release = UnitQuoteRelease.model_validate_json(
            _canonical(_object(payload["release_snapshot"])),
        )
        bindings = TypeAdapter(tuple[DapaneQuoteBinding, ...]).validate_json(
            _canonical(_array(payload["bindings"])),
        )
    except KeyError as error:
        message = "Quotation artifact lacks required snapshot or bindings"
        raise ValueError(message) from error
    if payload != export_dapane_quotes(release, bindings):
        message = "Quotation artifact differs from its validated release and bindings"
        raise ValueError(message)
    return payload


def _exact(value: Decimal | Fraction) -> JsonValue:
    """Encode the supplied number exactly; this performs no valuation."""
    if isinstance(value, Fraction):
        return {
            "numerator": _unsigned_integer(value.numerator),
            "denominator": _unsigned_integer(value.denominator),
        }
    return _decimal(value)


def build_dapane_request(
    artifact_json: str,
    quantities: tuple[QuoteQuantity, ...],
    *,
    expected_sha256: str,
    run_id: str,
    knowledge_cutoff: date,
) -> JsonObject:
    """Construct one shared-kernel request from explicit provider exposures."""
    artifact = load_dapane_quotes_json(artifact_json, expected_sha256=expected_sha256)
    quantities = tuple(QuoteQuantity.model_validate(dict(item)) for item in quantities)
    quotes = [_object(item) for item in _array(artifact["quotes"])]
    by_id = {_string(quote["id"]): quote for quote in quotes}
    if type(knowledge_cutoff) is not date:
        message = "Knowledge cutoff must be a date without an implicit time zone"
        raise TypeError(message)
    if knowledge_cutoff.isoformat() < _string(artifact["as_known_on"]):
        message = "Knowledge cutoff precedes the selected release"
        raise ValueError(message)
    usage: list[JsonValue] = []
    for quantity in quantities:
        quote = by_id.get(quantity.quote_id)
        if quote is None or quote["unit"] != quantity.unit:
            message = "Quantity requires an exported quote with the same unit"
            raise ValueError(message)
        usage.append(
            {
                "id": quantity.quantity_id,
                "use_id": quantity.quantity_id,
                "kind": "resource_use",
                "target": quote["target"],
                "unit": quantity.unit,
                "quantity": _exact(quantity.quantity),
                "service_date": quantity.valued_on.isoformat(),
                "quote_id": quantity.quote_id,
                "source": {
                    "id": quantity.quantity_id,
                    "version": "1",
                    "evidence": (
                        "synthetic"
                        if quantity.quantity_kind == "analyst_assumption"
                        else "observed"
                    ),
                    "access": "public",
                    "validation": "unvalidated",
                    "locator": quantity.basis,
                },
            },
        )
    first = quotes[0]
    return {
        "schema_version": "0.1",
        "run_id": run_id,
        "knowledge_cutoff": knowledge_cutoff.isoformat(),
        "policy": {
            "id": "workforce-public-reference",
            "version": "1",
            "currency": first["currency"],
            "price_year": first["price_year"],
            "perspective": "provider",
            "basis": "financial_cost",
            "rounding": {"scale": 2, "mode": "half_even"},
        },
        "quotes": cast("list[JsonValue]", quotes),
        "usage": usage,
    }


class _Kernel(Protocol):
    """Structural interface of the optional independently installed package."""

    def evaluate(self, request: JsonObject) -> JsonObject:
        """Delegate all valuation and allocation to Dapane's native binding."""
        ...


def evaluate_dapane(
    artifact_json: str,
    quantities: tuple[QuoteQuantity, ...],
    *,
    expected_sha256: str,
    run_id: str,
    knowledge_cutoff: date,
) -> JsonObject:
    """Evaluate via optional installed Dapane, with no Python fallback formula."""
    request = build_dapane_request(
        artifact_json,
        quantities,
        expected_sha256=expected_sha256,
        run_id=run_id,
        knowledge_cutoff=knowledge_cutoff,
    )
    kernel = cast("_Kernel", import_module("dapane"))
    return kernel.evaluate(request)
