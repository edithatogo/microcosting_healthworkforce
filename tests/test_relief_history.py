# Copyright 2026 Dylan. SPDX-License-Identifier: Apache-2.0
"""Exercise the working-day threshold and full relief period independently."""

from datetime import date, timedelta

import pytest

from src.relief_history import ReliefDay, ReliefRule, ReliefSpell, qualify_relief
from src.source_registry import SourceRegistry
from tests.checks import assert_that
from tests.test_source_registry import source


def test_relief_counts_workdays_and_qualifies_from_start() -> None:
    """Friday through Tuesday contains three declared working days."""
    start = date(2026, 7, 10)
    stop = date(2026, 7, 15)
    cutoff = date(2026, 7, 15)
    rule = ReliefRule(
        rule_id="fictional-relief",
        source_id="synthetic-award-1",
        source_sha256="a" * 64,
        citation="Fictional minimum-pay rule",
        jurisdiction="QLD",
        employer="Synthetic employer",
        classification="Synthetic grade",
        effective_from=start,
        effective_to=stop,
        minimum_working_days=3,
        activation_basis="Fictional reviewed operative interval",
    )
    days = tuple(
        ReliefDay(
            day=start + timedelta(days=offset),
            working_day=offset in (0, 3, 4),
            appointment_continued=True,
            whole_duties_and_responsibilities=offset in (0, 3, 4),
            evidence_id=f"fictional-day-{offset}",
            known_on=cutoff,
        )
        for offset in range(5)
    )
    spell = ReliefSpell(
        spell_id="fictional-appointment",
        starts_on=start,
        ends_on=stop,
        as_known_on=cutoff,
        appointment_evidence_id="fictional-appointment-evidence",
        days=days,
    )
    sources = SourceRegistry(records=(source(),))
    result = qualify_relief(rule, spell, sources)
    assert_that(result.threshold_met_on == date(2026, 7, 14))
    assert_that((result.payable_from, result.payable_to) == (start, stop))
    stricter = rule.model_copy(update={"minimum_working_days": 5})
    assert_that(qualify_relief(stricter, spell, sources).payable_from is None)
    broken = (
        days[0],
        days[1].model_copy(update={"appointment_continued": False}),
        *days[2:],
    )
    assert_that(
        qualify_relief(
            rule,
            spell.model_copy(update={"days": broken}),
            sources,
        ).payable_from
        is None,
    )
    with pytest.raises(ValueError, match="complete calendar-day"):
        qualify_relief(rule, spell.model_copy(update={"days": days[:-1]}), sources)
