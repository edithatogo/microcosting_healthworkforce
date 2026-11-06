# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Versioned candidate mappings for archived long-form sensitivity tables."""

from src.workbook_tables import ColumnMeaning, TableDefinition

WORKBOOK_SHA256 = "c72a5f9d8a232ee559516978537a7efdd1aea6df55738e9d851840fff837ddca"


def archive_table_definitions(workbook_sha256: str) -> tuple[TableDefinition, ...]:
    """Keep archived deterministic bounds separate from probabilistic outputs."""
    if workbook_sha256 != WORKBOOK_SHA256:
        msg = "Archive mapping requires the reviewed workbook SHA-256"
        raise ValueError(msg)
    identity = (
        ColumnMeaning("A", "personnel_type", None, "identity"),
        ColumnMeaning("B", "jurisdiction", None, "identity"),
        ColumnMeaning("C", "sensitivity_variable", None, "identity"),
    )
    annual = (
        ColumnMeaning("D", "annual_lower", "AUD/year", "archived_bound"),
        ColumnMeaning("E", "annual_midpoint", "AUD/year", "archived_bound"),
        ColumnMeaning("F", "annual_upper", "AUD/year", "archived_bound"),
    )
    hourly = (
        ColumnMeaning("D", "hourly_lower", "AUD/hour", "archived_bound"),
        ColumnMeaning("E", "hourly_midpoint", "AUD/hour", "archived_bound"),
        ColumnMeaning("F", "hourly_upper", "AUD/hour", "archived_bound"),
    )
    paired_hourly = (
        ColumnMeaning("G", "hourly_lower", "AUD/hour", "archived_bound"),
        ColumnMeaning("H", "hourly_midpoint", "AUD/hour", "archived_bound"),
        ColumnMeaning("I", "hourly_upper", "AUD/hour", "archived_bound"),
    )
    return (
        TableDefinition(
            "dsa_annual_hourly_long",
            "Labour - Prices (DSA,Val,Long)",
            "A1:I332",
            "archived_candidate",
            "Historical deterministic sensitivity outputs",
            (*identity, *annual, *paired_hourly),
            (1, 2),
        ),
        TableDefinition(
            "dsa_hourly_long",
            "Labour - Prices (DSA,Val,Lo (2)",
            "A1:F331",
            "archived_candidate",
            "Separate historical hourly sensitivity archive",
            (*identity, *hourly),
            (1,),
        ),
        TableDefinition(
            "psa_labelled_annual_long",
            "Labour - Pr (PSA,Val,Long,Tot)",
            "A1:F331",
            "archived_candidate",
            "PSA-labelled historical sensitivity bounds, not PSA draws",
            (*identity, *annual),
            (1,),
        ),
        TableDefinition(
            "psa_labelled_hourly_baseline",
            "Labour - Pr (PSA,Val,Hr)",
            "A1:F31",
            "archived_candidate",
            "PSA-labelled baseline bounds, not PSA draws",
            (*identity, *hourly),
            (1,),
        ),
    )
