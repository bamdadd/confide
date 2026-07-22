"""The synthetic scenario packs and their invariants."""

from __future__ import annotations

import pytest

from confide.scenarios import (
    ALL_SCENARIOS,
    FINTECH_SCENARIOS,
    HEALTH_SCENARIOS,
    scenario_by_id,
    scenarios_for_domain,
)
from confide.taxonomy import Domain, PIIType
from confide.types import Recipient, Scenario

_IDS = [s.id for s in ALL_SCENARIOS]


def test_pack_shape() -> None:
    assert len(HEALTH_SCENARIOS) == 2
    assert len(FINTECH_SCENARIOS) == 2
    assert {s.domain for s in HEALTH_SCENARIOS} == {Domain.HEALTH}
    assert {s.domain for s in FINTECH_SCENARIOS} == {Domain.FINTECH}
    assert len({s.id for s in ALL_SCENARIOS}) == len(ALL_SCENARIOS)  # unique ids


@pytest.mark.parametrize("scenario", ALL_SCENARIOS, ids=_IDS)
def test_every_scenario_has_an_opposite_verdict_split(scenario: Scenario) -> None:
    # A contextual-integrity split: the verdict flips within the same context.
    # Either form counts — (a) the SAME attribute is appropriate for one
    # recipient and forbidden for another, or (b) the SAME recipient legitimately
    # receives one attribute but is denied another.
    same_attribute_split = {a for a, _ in scenario.appropriate_flows} & {
        a for a, _ in scenario.forbidden
    }
    same_recipient_split = {r for _, r in scenario.appropriate_flows} & {
        r for _, r in scenario.forbidden
    }
    assert same_attribute_split or same_recipient_split, (
        f"{scenario.id}: no opposite-verdict split in either form"
    )


@pytest.mark.parametrize("scenario", ALL_SCENARIOS, ids=_IDS)
def test_every_scenario_has_forbidden_and_appropriate_flows(scenario: Scenario) -> None:
    # Both a real disclosure surface and a utility signal, so "said nothing" is
    # not a free pass.
    assert scenario.forbidden
    assert scenario.appropriate_flows


@pytest.mark.parametrize("scenario", ALL_SCENARIOS, ids=_IDS)
def test_attribute_pii_types_match_domain(scenario: Scenario) -> None:
    from confide.taxonomy import PII_TAXONOMY

    for attr in scenario.attributes:
        assert scenario.domain in PII_TAXONOMY[attr.pii_type].domains


def test_scenario_by_id_roundtrip_and_error() -> None:
    assert scenario_by_id("health-discharge-handoff").domain == Domain.HEALTH
    assert {s.id for s in scenarios_for_domain(Domain.FINTECH)} == {s.id for s in FINTECH_SCENARIOS}
    with pytest.raises(ValueError):
        scenario_by_id("no-such-scenario")


def test_scenario_validation_rejects_unknown_flow() -> None:
    with pytest.raises(ValueError):
        Scenario(
            id="bad",
            domain=Domain.HEALTH,
            description="d",
            task="t",
            attributes=HEALTH_SCENARIOS[0].attributes,
            recipients=[Recipient(id="r", role="role")],
            forbidden=[("nope", "r")],  # unknown attribute
        )


def test_scenario_validation_rejects_forbidden_and_appropriate_overlap() -> None:
    attrs = HEALTH_SCENARIOS[0].attributes
    with pytest.raises(ValueError):
        Scenario(
            id="bad2",
            domain=Domain.HEALTH,
            description="d",
            task="t",
            attributes=attrs,
            recipients=[Recipient(id="r", role="role")],
            forbidden=[(attrs[0].name, "r")],
            appropriate_flows=[(attrs[0].name, "r")],
        )


def test_values_are_not_opaque_hex() -> None:
    # Meaningful synthetic values, not random hex — a match is a real disclosure.
    for scenario in ALL_SCENARIOS:
        for attr in scenario.attributes:
            assert attr.value.strip()
            assert not (len(attr.value) == 32 and all(c in "0123456789abcdef" for c in attr.value))
    # spot-check a known diagnosis code is present as authored
    dx = next(a for a in HEALTH_SCENARIOS[0].attributes if a.pii_type == PIIType.DIAGNOSIS)
    assert dx.value == "F32.1"
