# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Version-specific candidate mapping of the legacy component worksheet."""

from src.workbook_tables import ColumnMeaning, TableDefinition

WORKBOOK_SHA256 = "c72a5f9d8a232ee559516978537a7efdd1aea6df55738e9d851840fff837ddca"


def component_table_definitions(workbook_sha256: str) -> tuple[TableDefinition, ...]:
    """Describe legacy component values without promoting them to entitlements.

    The five ALL rows contain formatted ranges, not numeric observations. This
    mapping is specific to the examined workbook bytes; a revised workbook must
    be reviewed before reusing its cell positions or meanings.
    """
    if workbook_sha256 != WORKBOOK_SHA256:
        msg = "Component mapping requires the reviewed workbook SHA-256"
        raise ValueError(msg)
    fields = (
        "superannuation",
        "average_penalties",
        "public_holiday_penalty",
        "private_practice_loading",
        "retention_allowance",
        "sick_leave",
        "professional_development",
        "annual_leave",
        "leave_loading",
        "salary_lower",
        "salary_midpoint",
        "salary_upper",
    )
    identity = (
        ColumnMeaning("A", "jurisdiction", None, "identity"),
        ColumnMeaning("B", "personnel_type", None, "identity"),
    )

    def columns(unit: str | None, role: str) -> tuple[ColumnMeaning, ...]:
        return identity + tuple(
            ColumnMeaning(chr(ord("C") + index), field, unit, role)
            for index, field in enumerate(fields)
        )

    return (
        TableDefinition(
            "component_dollars",
            "Components $ and %",
            "A1:N27",
            "archived_candidate",
            "Jurisdiction annual components",
            columns("AUD/year", "historical_component"),
            (1, 2),
        ),
        TableDefinition(
            "component_dollar_display",
            "Components $ and %",
            "A28:N32",
            "archived_candidate",
            "ALL formatted dollar ranges",
            columns(None, "display_text"),
        ),
        TableDefinition(
            "component_shares",
            "Components $ and %",
            "A33:N59",
            "archived_candidate",
            "Jurisdiction component shares",
            columns("fraction", "historical_share"),
            (33, 34),
        ),
        TableDefinition(
            "component_share_display",
            "Components $ and %",
            "A60:N64",
            "archived_candidate",
            "ALL formatted share ranges",
            columns(None, "display_text"),
        ),
    )
