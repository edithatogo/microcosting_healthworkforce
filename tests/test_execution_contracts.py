# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Exercise runtime schema checks through the actual Polars backend."""

import polars as pl
import pytest
from pandera.errors import SchemaError

from src.workbook_run import PSA_SCHEMA


def test_positive_iteration_contract() -> None:
    """Accept positive iterations and reject zero and duplicate identifiers."""
    PSA_SCHEMA.validate(pl.DataFrame({"iteration": [1, 2], "mean_cost": [1.0, 2.0]}))
    for iterations in ([0, 1], [1, 1]):
        with pytest.raises(SchemaError):
            PSA_SCHEMA.validate(
                pl.DataFrame({"iteration": iterations, "mean_cost": [1.0, 2.0]}),
            )
