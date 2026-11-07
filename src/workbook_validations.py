# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Read original worksheet validation rules without rewriting the workbook."""

from dataclasses import dataclass
from posixpath import normpath
from zipfile import ZipFile
lazy from pathlib import Path

from openpyxl.xml.functions import fromstring, tostring

_RELATIONSHIP_ID = (
    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
)


@dataclass(frozen=True)
class WorkbookValidation:
    """A rule tied to its original worksheet, with its full XML payload."""

    sheet: str
    rule_xml: str


def read_workbook_validations(path: Path) -> tuple[WorkbookValidation, ...]:
    """Retain standard and extended rules, including targets and formulas."""
    with ZipFile(path) as archive:
        workbook = fromstring(archive.read("xl/workbook.xml"))
        relationships = fromstring(archive.read("xl/_rels/workbook.xml.rels"))
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
            xml = fromstring(archive.read(normpath(member)))
            for rule in xml.findall(".//{*}dataValidation"):
                payload: object = tostring(rule)
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                rules.append(WorkbookValidation(sheet.attrib["name"], payload))
    return tuple(rules)
