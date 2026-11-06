# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Exercise command-line argument handling without a workbook mutation."""

import argparse
import logging
lazy from pathlib import Path

import polars as pl
import pytest
lazy from _pytest.logging import LogCaptureFixture

from src.main import main
from src.workbook_run import WorkforceRun
from tests.checks import assert_that


def test_workforce_runner_reports_exploratory_psa(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: LogCaptureFixture,
) -> None:
    """The production PSA runner must expose the exploratory qualification."""
    scenarios = tmp_path / "scenarios.json"
    scenarios.write_text("[]")
    monkeypatch.setattr(
        "src.workbook_run.config.PSA_SCENARIOS_FILE_PATH",
        str(scenarios),
    )

    def synthetic_psa(*_args: object, **_kwargs: object) -> pl.DataFrame:
        return pl.DataFrame({"iteration": [1], "mean_cost": [100.0]})

    def skip_plot(*_args: object) -> None:
        return None

    monkeypatch.setattr(
        "src.workbook_run.run_psa_analysis",
        synthetic_psa,
    )
    monkeypatch.setattr("src.workbook_run.plot_psa", skip_plot)
    runner = WorkforceRun(
        argparse.Namespace(output_dir=str(tmp_path), psa_iterations=1, seed=1),
    )
    runner.frame = pl.DataFrame({"value": [1]})
    runner.formulas = {"formulas": [], "outputs": []}
    with caplog.at_level(logging.INFO):
        runner.run_psa()
    assert_that("Exploratory PSA" in caplog.text)
    assert_that("not scientifically validated" in caplog.text)
    assert_that((tmp_path / "psa_results.csv").is_file())


def test_main_does_not_raise_exceptions(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise CLI help independently of pytest's own command-line arguments."""
    monkeypatch.setattr("sys.argv", ["microcosting-healthworkforce", "--help"])
    with pytest.raises(SystemExit, match=r"^0$"):
        main()
