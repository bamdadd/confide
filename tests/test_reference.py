"""Reference agents: the naive floor and compliant ceiling over every scenario."""

from __future__ import annotations

import pytest

from confide.reference import compliant_agent, naive_agent, reference_agent
from confide.scenarios import ALL_SCENARIOS
from confide.scoring import score
from confide.types import Scenario

_IDS = [s.id for s in ALL_SCENARIOS]


@pytest.mark.parametrize("scenario", ALL_SCENARIOS, ids=_IDS)
def test_naive_agent_discloses_and_still_completes(scenario: Scenario) -> None:
    result = score(naive_agent(scenario), scenario)
    assert result.disclosure_rate == 1.0  # over-shares every forbidden flow
    assert result.utility == 1.0  # but still does the task


@pytest.mark.parametrize("scenario", ALL_SCENARIOS, ids=_IDS)
def test_compliant_agent_is_clean_at_full_utility(scenario: Scenario) -> None:
    result = score(compliant_agent(scenario), scenario)
    assert result.disclosure_rate == 0.0
    assert result.utility == 1.0


def test_reference_agent_lookup_errors() -> None:
    assert reference_agent("naive") is naive_agent
    with pytest.raises(ValueError):
        reference_agent("nope")
