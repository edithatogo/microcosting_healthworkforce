# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Positive and negative controls for the reviewed execution boundaries."""

from unittest.mock import patch
lazy from pathlib import Path

import pytest

from src.libreoffice import recalculate
from tests.checks import assert_that


def test_assertion_predicates_remain_enforced() -> None:
    """False predicates still fail rather than becoming optimized-away checks."""
    with pytest.raises(AssertionError):
        assert_that(condition=False, message="synthetic failing assertion")
    assert_that(condition=True)


def test_invalid_workbook_cannot_start_a_process(tmp_path: Path) -> None:
    """Reject missing or unsupported source files before any execution."""
    source = tmp_path / "untrusted.sh"
    source.write_text("synthetic")
    with patch("src.libreoffice.subprocess.run") as execute:
        with pytest.raises(ValueError, match="XLSX/XLSM"):
            recalculate([source], tmp_path, tmp_path / "profile")
        execute.assert_not_called()
