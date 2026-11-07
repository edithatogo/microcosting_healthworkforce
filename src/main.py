# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Run the workforce workbook model from the command line."""

import argparse
import cProfile

from src.workbook_run import run


def _setup_arg_parser() -> argparse.ArgumentParser:
    """Set up the argument parser for the command-line interface.

    Returns:
        An argparse.ArgumentParser instance.

    """
    parser = argparse.ArgumentParser(
        description="Data-driven calculation engine for health workforce microcosting.",
    )
    parser.add_argument(
        "--dsa-scenarios",
        type=str,
        help="Path to a custom JSON file with DSA scenarios.",
    )
    parser.add_argument(
        "--run-psa",
        action="store_true",
        help="Run the Probabilistic Sensitivity Analysis (PSA).",
    )
    parser.add_argument(
        "--psa-iterations",
        type=int,
        default=1000,
        help="Number of iterations for the PSA.",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Enable profiling.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=".",
        help="Directory to save output files.",
    )
    parser.add_argument(
        "--no-dsa-validation",
        action="store_true",
        help="Disable DSA validation.",
    )
    parser.add_argument(
        "--workbook-projection",
        action="store_true",
        help="Use workbook simple indexation for the four base-case projection years.",
    )
    parser.add_argument("--seed", type=int, default=20261103)
    return parser


def main() -> None:
    """Run the selected workload, optionally recording a CPU profile."""
    args = _setup_arg_parser().parse_args()
    if args.profile:
        cProfile.runctx("run(args)", globals(), locals(), sort="cumulative")
    else:
        run(args)


if __name__ == "__main__":
    main()
