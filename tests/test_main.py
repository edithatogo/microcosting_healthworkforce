# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Exercise command-line argument handling without a workbook mutation."""

import pytest

from src.main import main


def test_main_does_not_raise_exceptions(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise CLI help independently of pytest's own command-line arguments."""
    monkeypatch.setattr("sys.argv", ["microcosting-healthworkforce", "--help"])
    with pytest.raises(SystemExit, match=r"^0$"):
        main()
