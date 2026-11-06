# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Polars execution of the delivered workforce model and its configured scenarios."""

import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any
lazy import argparse

import matplotlib.pyplot as plt
import openpyxl
import pandera.polars as pa
import polars as pl

if TYPE_CHECKING:
    from pandera.api.polars.types import PolarsData

    from src.contracts import FormulaDocument

from src import config
from src.formula_engine import apply_formulas, load_formulas
from src.libreoffice import recalculate
from src.numeric import numeric, row_filter
from src.projection import project_costs
from src.psa_analysis import report_psa_results, run_psa_analysis
from src.psa_simulation import SimulationSpec
from src.rate_converter import convert_annual_cost_to_rates
from src.scenario_oracle import compare_scenarios


def positive_iterations(data: PolarsData) -> pl.LazyFrame:
    """Require every stored simulation iteration to be positive."""
    return data.lazyframe.select(pl.col(data.key) > 0)


PSA_SCHEMA = pa.DataFrameSchema(
    {
        "iteration": pa.Column(int, checks=pa.Check(positive_iterations), unique=True),
        "mean_cost": pa.Column(float),
    },
    strict=True,
)


def parameters(workbook: openpyxl.Workbook) -> pl.DataFrame:
    """Extract the 25 uniquely keyed workforce rows from the recalculated workbook."""
    rows = list(workbook[config.LABOUR_PRICES_SHEET].values)
    mapping = json.loads(Path(config.FORMULAS_FILE_PATH).read_text())["outputs"][1][
        "parameter_mapping"
    ]
    records: list[dict[str, object]] = []
    for r in rows[3:32]:
        if not r[0] or not r[1]:
            continue
        record: dict[str, object] = {"Jurisdiction": r[0], "Personnel type": r[1]}
        for i in range(9, 21):
            record["Grade(s)_" + str(rows[2][i])] = r[i] or 0
        for i, tier in enumerate(("LL", "Mid-point", "UL")):
            record["Base Salary_" + tier] = r[21 + i]
            record["Base Salary + Costs_" + tier] = r[24 + i]
            record["Base Salary + Costs (hourly)_" + tier] = r[27 + i]
        records.append(record)
    frame = pl.DataFrame(records)
    if (
        frame.height != config.EXPECTED_STATE_ROLE_ROWS
        or frame.select("Jurisdiction", "Personnel type").is_duplicated().any()
        or set(mapping.values()) - set(frame.columns)
    ):
        message = "Unsupported workforce input layout"
        raise ValueError(message)
    if frame.select(pl.col("Base Salary_Mid-point").is_null().any()).item():
        message = "Workbook requires recalculation"
        raise ValueError(message)
    return frame


class WorkforceRun:
    """Retain one run's state across bounded, separately validated stages."""

    frame: pl.DataFrame
    formulas: FormulaDocument
    mapping: dict[str, str]
    values: list[tuple[object, ...]]
    validations: list[dict[str, str | float | bool]]
    oracle_inputs: list[tuple[str, pl.DataFrame, dict[str, Any], dict[str, str]]]

    def __init__(self, args: argparse.Namespace) -> None:
        """Retain the command specification and initial empty validation lists."""
        self.args = args
        self.dest = Path(args.output_dir)
        self.source = Path(config.DATA_FILE_PATH)
        self.validations = []
        self.oracle_inputs = []

    def prepare(self) -> None:
        """Recalculate a source copy and retain its delivered validation cells."""
        self.dest.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            recalculate([self.source], root, root / "profile")
            book = openpyxl.load_workbook(
                root / self.source.name,
                read_only=True,
                data_only=True,
            )
            try:
                self.frame = parameters(book)
                self.values = list(book[config.DSA_VALIDATION_SHEET].values)
            finally:
                book.close()
        self.formulas = load_formulas(config.FORMULAS_FILE_PATH)
        primary_output = self.formulas["outputs"][1]
        if "parameter_mapping" not in primary_output:
            message = "Primary workforce output has no parameter mapping"
            raise ValueError(message)
        self.mapping = primary_output["parameter_mapping"]

    def calculate(self, data: pl.DataFrame) -> pl.DataFrame:
        """Apply the unchanged calculation, projection and rate pipeline."""
        return convert_annual_cost_to_rates(
            project_costs(
                apply_formulas(data, self.formulas),
                data,
                config.PROJECTION_YEARS,
            ),
            data,
        )

    def validate_baseline(self, result: pl.DataFrame) -> None:
        """Retain the source-backed baseline parity rejection."""
        difference = (
            (
                result["Calculated_Cost_Mid_Y0"]
                - self.frame["Base Salary + Costs_Mid-point"]
            )
            .abs()
            .max()
        )
        if numeric(difference) > config.PARITY_TOLERANCE:
            message = "Workforce workbook base case disagrees"
            raise ValueError(message)

    def scenario_data(self, scenario: dict[str, Any]) -> pl.DataFrame:
        """Apply declared row masks and perturbations without changing the base."""
        name = scenario["name"]
        if Path(name).name != name:
            message = "Unsafe scenario filename"
            raise ValueError(message)
        data = self.frame
        mask = pl.lit(value=True)
        for col, value in row_filter(scenario.get("row_filter")).items():
            mask = mask & (pl.col(col) == value)
        for param, variation in zip(
            scenario.get("parameters_to_vary", [scenario.get("parameter_to_vary")]),
            scenario.get("variations", [scenario.get("variation")]),
            strict=True,
        ):
            col = self.mapping[param]
            if variation["type"] == "percentage":
                expr = pl.col(col) * (1 + variation["value"])
            elif variation["type"] == "absolute":
                expr = pl.col(col) + variation["value"]
            else:
                message = "Unknown scenario type"
                raise ValueError(message)
            data = data.with_columns(
                pl.when(mask).then(expr).otherwise(pl.col(col)).alias(col),
            )
        return data

    def validate_delivered_scenario(self, name: str, changed: pl.DataFrame) -> None:
        """Compare the same delivered workbook cells for mapped scenarios."""
        target = config.DSA_SCENARIO_VALIDATION_MAPPING.get(name)
        if not target:
            return
        group = target.split("_")[0]
        index = next((i + 1 for i, g in enumerate(self.values[0]) if g == group), None)
        if index is None:
            return
        lookup = {(r[0], r[1]): r[index] for r in self.values[3:28]}
        diff = [
            abs(
                numeric(row["Calculated_Cost_Mid_Y0"])
                - numeric(lookup[row["Jurisdiction"], row["Personnel type"]]),
            )
            for row in changed.iter_rows(named=True)
        ]
        self.validations.append(
            {
                "scenario": name,
                "maximum_difference": max(diff),
                "within_cent": max(diff) < config.PARITY_TOLERANCE,
            },
        )

    def run_dsa(self, result: pl.DataFrame) -> None:
        """Save declared sensitivities, retaining all validation comparisons."""
        reference = mean_cost(result)
        summary: list[dict[str, str | float]] = []
        details = self.dest / "dsa_detailed"
        details.mkdir(exist_ok=True)
        for scenario in json.loads(
            Path(self.args.dsa_scenarios or config.DSA_SCENARIOS_FILE_PATH).read_text(),
        ):
            name = scenario["name"]
            changed = self.calculate(self.scenario_data(scenario))
            changed.write_csv(details / (name + ".csv"))
            avg = mean_cost(changed)
            summary.append(
                {
                    "scenario_name": name,
                    "base_case_cost": reference,
                    "scenario_cost": avg,
                    "percentage_change": 100 * (avg / reference - 1),
                },
            )
            self.oracle_inputs.append((name, changed, scenario, self.mapping))
            self.validate_delivered_scenario(name, changed)
        table = pl.DataFrame(summary).sort("percentage_change")
        table.write_csv(self.dest / "dsa_summary.csv")
        plot_dsa(table, self.dest)

    def run_psa(self) -> None:
        """Retain the seeded distributions and positive-iteration contract."""
        spec = SimulationSpec(iterations=self.args.psa_iterations, seed=self.args.seed)
        scenarios = json.loads(Path(config.PSA_SCENARIOS_FILE_PATH).read_text())
        simulations = run_psa_analysis(
            self.frame,
            dict(self.formulas),
            apply_formulas,
            scenarios,
            spec.iterations,
            seed=spec.seed,
        )
        psa = PSA_SCHEMA.validate(simulations)
        report_psa_results(psa)
        psa.write_csv(self.dest / "psa_results.csv")
        plot_psa(psa, self.dest)

    def verify(self) -> None:
        """Require all independent scenario-oracle comparisons to pass."""
        baseline = {
            (row["Jurisdiction"], row["Personnel type"]): row
            for row in self.frame.iter_rows(named=True)
        }
        verified = compare_scenarios(self.source, self.oracle_inputs, baseline)
        archive_path = self.dest / "archived_dsa_comparison.csv"
        pl.DataFrame(self.validations).write_csv(archive_path)
        verified.write_csv(self.dest / "dsa_validation.csv")
        if (
            verified.height != len(self.oracle_inputs)
            or not verified["within_cent"].all()
        ):
            message = "Recalculated scenario parity not established"
            raise ValueError(message)
        (self.dest / "delivered_validation.json").write_text(
            json.dumps(self.validations, indent=2),
        )


def mean_cost(data: pl.DataFrame) -> float:
    """Keep the original unweighted mean of the workforce rows."""
    return numeric(data["Calculated_Cost_Mid_Y0"].mean())


def plot_dsa(table: pl.DataFrame, dest: Path) -> None:
    """Render exactly the saved scenario percentage-change table."""
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(table["scenario_name"].to_list(), table["percentage_change"].to_list())
    ax.set_xlabel("Change in mean cost (%)")
    fig.tight_layout()
    fig.savefig(dest / "dsa_tornado_plot.png")
    plt.close(fig)


def run(args: argparse.Namespace) -> None:
    """Execute all original stages and their workbook acceptance checks."""
    execution = WorkforceRun(args)
    execution.prepare()
    result = execution.calculate(execution.frame)
    result.write_csv(execution.dest / "base_case_results.csv")
    execution.validate_baseline(result)
    execution.run_dsa(result)
    if args.run_psa:
        execution.run_psa()
    if not args.no_dsa_validation:
        execution.verify()


def plot_psa(psa: pl.DataFrame, dest: Path) -> None:
    """Retain the original histogram and filename for the saved draws."""
    fig, ax = plt.subplots()
    ax.hist(psa["mean_cost"].to_list())
    ax.set_xlabel("Mean cost")
    fig.savefig(dest / "psa_histogram.png")
    plt.close(fig)
