import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src.main import main


def test_main_end_to_end(tmp_path: Path) -> None:
    """
    Tests the main function end-to-end, checking for output file creation.
    """
    # Create a temporary directory for output files
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()

    # Mock sys.argv to run the main script with specific arguments
    test_args = [
        "script_name",
        "--output-dir",
        str(output_dir),
        "--run-psa",
        "--psa-iterations",
        "10",  # Use a small number of iterations for testing
        "--no-dsa-validation",
    ]

    with patch.object(sys, "argv", test_args):
        main()

    # Check that the expected output files were created
    assert (output_dir / "base_case_results.csv").exists()
    assert (output_dir / "dsa_summary.csv").exists()
    assert (output_dir / "psa_results.csv").exists()
    assert (output_dir / "dsa_tornado_plot.png").exists()
    assert (output_dir / "psa_histogram.png").exists()

    # Optionally, check the content of the created files
    base_case_df = pd.read_csv(output_dir / "base_case_results.csv")
    assert not base_case_df.empty
    assert "Personnel type" in base_case_df.columns

    dsa_summary_df = pd.read_csv(output_dir / "dsa_summary.csv")
    assert not dsa_summary_df.empty
    assert "scenario_name" in dsa_summary_df.columns

    psa_results_df = pd.read_csv(output_dir / "psa_results.csv")
    assert not psa_results_df.empty
    assert "iteration" in psa_results_df.columns
