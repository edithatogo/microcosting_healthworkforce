# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Read original worksheet validation rules without rewriting the workbook."""

from dataclasses import dataclass
from posixpath import normpath
from zipfile import ZipFile
lazy from pathlib import Path

from openpyxl.formula.translate import Translator
from openpyxl.utils.cell import get_column_letter
from openpyxl.worksheet.cell_range import CellRange
from openpyxl.xml.functions import fromstring, tostring

_RELATIONSHIP_ID = (
    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
)


@dataclass(frozen=True)
class WorkbookValidation:
    """A rule tied to its original worksheet, with its full XML payload."""

    sheet: str
    rule_xml: str
    targets: tuple[str, ...] = ()
    formula1: str | None = None
    formula2: str | None = None

    def formulas_at(self, cell: str) -> tuple[str | None, str | None]:
        """Translate operands within one contiguous validation range."""
        if len(self.targets) != 1:
            msg = "Formula translation requires a single validation range"
            raise ValueError(msg)
        target = CellRange(self.targets[0])
        if cell not in target:
            msg = "Cell is outside the validation range"
            raise ValueError(msg)
        origin = f"{get_column_letter(target.min_col)}{target.min_row}"

        def translate(formula: str | None) -> str | None:
            if formula is None:
                return None
            expression = "=" + formula.removeprefix("=")
            result: str = Translator(expression, origin=origin).translate_formula(cell)
            return result if formula.startswith("=") else result.removeprefix("=")

        return translate(self.formula1), translate(self.formula2)


def _read_xml_part(archive: ZipFile, member: str) -> bytes:
    data = archive.read(member)
    if b"<!DOCTYPE" in data.replace(b"\x00", b""):
        msg = "Workbook XML must not contain a document type declaration"
        raise ValueError(msg)
    return data


def read_workbook_validations(path: Path) -> tuple[WorkbookValidation, ...]:
    """Retain standard and extended rules, including targets and formulas."""
    with ZipFile(path) as archive:
        workbook = fromstring(_read_xml_part(archive, "xl/workbook.xml"))
        relationships = fromstring(
            _read_xml_part(archive, "xl/_rels/workbook.xml.rels"),
        )
        targets = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in relationships
            if rel.attrib.get("Type", "").endswith("/worksheet")
        }
        rules: list[WorkbookValidation] = []
        for sheet in workbook.findall(".//{*}sheet"):
            target = targets.get(sheet.attrib[_RELATIONSHIP_ID])
            if target is None:
                continue
            member = target.lstrip("/") if target.startswith("/") else f"xl/{target}"
            xml = fromstring(_read_xml_part(archive, normpath(member)))
            for rule in xml.findall(".//{*}dataValidation"):
                payload: object = tostring(rule)
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                target_ranges = rule.get("sqref") or rule.findtext("{*}sqref") or ""
                rules.append(
                    WorkbookValidation(
                        sheet.attrib["name"],
                        payload,
                        tuple(target_ranges.split()),
                        rule.findtext("{*}formula1/{*}f")
                        or rule.findtext("{*}formula1"),
                        rule.findtext("{*}formula2/{*}f")
                        or rule.findtext("{*}formula2"),
                    ),
                )
    return tuple(rules)
