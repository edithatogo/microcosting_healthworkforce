# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Recalculate local workbooks using explicit supported LibreOffice executables."""

import subprocess  # nosec B404 - fixed executable paths, separate arguments
from pathlib import Path


def recalculate(sources: list[Path], target: Path, profile: Path) -> None:
    """Validate workbook arguments and run the supported native conversion."""
    if not sources or any(
        not p.is_file() or p.suffix.lower() not in {".xlsx", ".xlsm"} for p in sources
    ):
        message = "Recalculation requires existing XLSX/XLSM source workbooks"
        raise ValueError(message)
    args = [
        "-env:UserInstallation=" + profile.resolve().as_uri(),
        "--headless",
        "--convert-to",
        "xlsx",
        "--outdir",
        str(target.resolve()),
        *(str(p.resolve()) for p in sources),
    ]
    if Path("/Applications/LibreOffice.app/Contents/MacOS/soffice").is_file():
        subprocess.run(  # noqa: S603  # nosec B603 - validated paths, fixed executable
            ["/Applications/LibreOffice.app/Contents/MacOS/soffice", *args],
            check=True,
            timeout=120,
            shell=False,
            capture_output=True,
        )
    elif Path("/usr/bin/libreoffice").is_file():
        subprocess.run(  # noqa: S603  # nosec B603 - validated paths, fixed executable
            ["/usr/bin/libreoffice", *args],
            check=True,
            timeout=120,
            shell=False,
            capture_output=True,
        )
    else:
        message = "Supported LibreOffice executable is unavailable"
        raise FileNotFoundError(message)
