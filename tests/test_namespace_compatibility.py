# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Legacy import order, class identity, pickle names and module entry points."""

import subprocess
import sys

import pytest

from tests.checks import assert_that


@pytest.mark.parametrize("first", ["src", "microcosting_healthworkforce"])
def test_legacy_and_canonical_import_orders_preserve_identity(first: str) -> None:
    """Fresh processes resolve both names to one model class and module."""
    code = """
import importlib
import pickle
import sys
from importlib.resources import files
first = sys.argv[1]
second = "src" if first != "src" else "microcosting_healthworkforce"
a = importlib.import_module(first + ".unit_quotes")
b = importlib.import_module(second + ".unit_quotes")
assert importlib.import_module(first) is importlib.import_module(second)
assert a is b
assert a.UnitQuoteRelease is b.UnitQuoteRelease
assert a.__spec__.name == "microcosting_healthworkforce.unit_quotes"
profile = "workbook_candidate_profile.json"
assert (
    files(first).joinpath(profile).read_bytes()
    == files(second).joinpath(profile).read_bytes()
)
old_class = pickle.loads(b"csrc.unit_quotes\\nUnitQuoteRelease\\n.")
assert old_class is a.UnitQuoteRelease
assert pickle.loads(pickle.dumps(a.UnitQuoteRelease)) is a.UnitQuoteRelease
"""
    result = subprocess.run(  # noqa: S603 - Fixed interpreter and test-owned code.
        [sys.executable, "-c", code, first],
        check=True,
        capture_output=True,
        text=True,
    )
    assert_that(result.returncode == 0)


@pytest.mark.parametrize(
    "module",
    [
        "src.main",
        "src.conditions_cli",
        "src.unit_quotes_cli",
        "src.leave_cli",
        "microcosting_healthworkforce.main",
        "microcosting_healthworkforce.conditions_cli",
        "microcosting_healthworkforce.unit_quotes_cli",
        "microcosting_healthworkforce.leave_cli",
    ],
)
def test_historical_and_canonical_module_entry_points(module: str) -> None:
    """Explicit module commands remain usable after namespace migration."""
    result = subprocess.run(  # noqa: S603 - Fixed interpreter and listed modules.
        [sys.executable, "-m", module, "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert_that("usage:" in result.stdout)
