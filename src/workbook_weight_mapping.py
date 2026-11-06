# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Candidate mapping for the original workbook's Medicare weighting inputs."""

from src.workbook_tables import ColumnMeaning, TableDefinition

WORKBOOK_SHA256 = "c72a5f9d8a232ee559516978537a7efdd1aea6df55738e9d851840fff837ddca"


def weight_table_definitions(workbook_sha256: str) -> tuple[TableDefinition, ...]:
    """Identify historical observations and formulas, not workforce weights."""
    if workbook_sha256 != WORKBOOK_SHA256:
        msg = "Weight mapping requires the reviewed workbook SHA-256"
        raise ValueError(msg)
    sheet = "Medicare Enrolments"
    jurisdictions = ("NSW", "VIC", "QLD", "SA", "WA", "TAS", "ACT", "NT", "Australia")

    def measures(unit: str, role: str) -> tuple[ColumnMeaning, ...]:
        return (
            ColumnMeaning("A", "measure", None, "label"),
            *(
                ColumnMeaning(chr(ord("B") + i), name, unit, role)
                for i, name in enumerate(jurisdictions)
            ),
        )

    return (
        TableDefinition(
            "medicare_metadata",
            sheet,
            "A1:A3",
            "archived_candidate",
            "Original source and date labels",
        ),
        TableDefinition(
            "medicare_card_distribution",
            sheet,
            "A5:J17",
            "archived_candidate",
            "Cards by persons on card",
            measures("cards", "historical_reference"),
            (5,),
        ),
        TableDefinition(
            "medicare_total_cards",
            sheet,
            "A18:J18",
            "archived_candidate",
            "Total cards",
            measures("cards", "historical_reference"),
        ),
        TableDefinition(
            "medicare_persons",
            sheet,
            "A19:J21",
            "archived_candidate",
            "Eligible persons and persons on cards, distinguished by row label",
            measures("persons", "historical_reference"),
        ),
        TableDefinition(
            "medicare_persons_per_card",
            sheet,
            "A22:J22",
            "archived_candidate",
            "Average persons per card",
            measures("persons/card", "historical_reference"),
        ),
        TableDefinition(
            "medicare_method_notes",
            sheet,
            "A23:A28",
            "archived_candidate",
            "Method and historical caveats",
        ),
        TableDefinition(
            "medicare_system_change",
            sheet,
            "A29:B37",
            "archived_candidate",
            "Signed eligible-person count change for September 2005; note A28",
            (
                ColumnMeaning("A", "jurisdiction", None, "identity"),
                ColumnMeaning(
                    "B",
                    "eligible_persons_method_change",
                    "persons",
                    "historical_method_change",
                ),
            ),
            (29,),
        ),
        TableDefinition(
            "medicare_disclaimer",
            sheet,
            "A38:A41",
            "archived_candidate",
            "Historical source and disclaimer notes",
        ),
        TableDefinition(
            "weight_headers",
            "Weightings",
            "A1:H1",
            "archived_candidate",
            "Original display labels",
        ),
        TableDefinition(
            "weight_all_jurisdictions",
            "Weightings",
            "A2:B9",
            "archived_candidate",
            "Eligible persons in all eight jurisdictions",
            (
                ColumnMeaning("A", "jurisdiction", None, "identity"),
                ColumnMeaning(
                    "B",
                    "eligible_persons",
                    "persons",
                    "historical_reference",
                ),
            ),
        ),
        TableDefinition(
            "weight_five_state_formulas",
            "Weightings",
            "C2:D6",
            "archived_candidate",
            "Five-state selection and normalised fractions",
            (
                ColumnMeaning("C", "selected_eligible_persons", "persons", "formula"),
                ColumnMeaning("D", "five_state_fraction", "fraction", "formula"),
            ),
        ),
        TableDefinition(
            "weight_totals",
            "Weightings",
            "A10:C10",
            "archived_candidate",
            "Australia count and distinct five-state denominator",
            (
                ColumnMeaning("A", "label", None, "label"),
                ColumnMeaning(
                    "B",
                    "australian_eligible_persons",
                    "persons",
                    "historical_reference",
                ),
                ColumnMeaning("C", "five_state_denominator", "persons", "formula"),
            ),
        ),
        TableDefinition(
            "weight_reordered",
            "Weightings",
            "F2:H6",
            "archived_candidate",
            "Reordered five-state observations and fractions",
            (
                ColumnMeaning("F", "jurisdiction", None, "identity"),
                ColumnMeaning(
                    "G",
                    "eligible_persons",
                    "persons",
                    "historical_reference",
                ),
                ColumnMeaning("H", "five_state_fraction", "fraction", "formula"),
            ),
        ),
        TableDefinition(
            "weight_fraction_sum",
            "Weightings",
            "H7:H7",
            "archived_candidate",
            "Sum of reordered fractions",
            (ColumnMeaning("H", "fraction_sum", "fraction", "formula"),),
        ),
    )
