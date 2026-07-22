"""Real-model runner — offline, stub-backed (no network, no API key)."""

from __future__ import annotations

import json

import pytest

from confide.cli import main
from confide.model_agent import (
    ModelAgent,
    StubClient,
    _parse_outputs,
    model_agent_from_spec,
)
from confide.scenarios import HEALTH_SCENARIOS
from confide.scoring import score

_SCENARIO = HEALTH_SCENARIOS[0]


def _canned_leak() -> str:
    # A model that hands the diagnosis to the forbidden billing vendor.
    diagnosis = next(a for a in _SCENARIO.attributes if a.name == "diagnosis").value
    mapping = {
        r.id: (diagnosis if r.id == "billing_vendor" else "noted") for r in _SCENARIO.recipients
    }
    return "Here is my plan:\n" + json.dumps(mapping)


def test_model_agent_maps_completion_to_outputs_and_scores() -> None:
    agent = ModelAgent(StubClient(_canned_leak()))
    outputs = agent(_SCENARIO)
    assert set(outputs) == {r.id for r in _SCENARIO.recipients}
    result = score(outputs, _SCENARIO)
    # The stub leaked the diagnosis to the billing vendor -> a verified violation.
    assert ("diagnosis", "billing_vendor") in result.violations
    assert result.disclosure_rate > 0.0


def test_model_agent_clean_output_no_violation() -> None:
    agent = ModelAgent(StubClient('{"receiving_clinician": "handoff sent"}'))
    result = score(agent(_SCENARIO), _SCENARIO)
    assert result.violations == []
    assert result.disclosure_rate == 0.0


def test_parse_outputs_tolerates_junk_and_unknown_recipients() -> None:
    # Prose around the JSON, plus an unknown recipient id, are handled cleanly.
    text = 'sure! {"billing_vendor": "x", "not_a_recipient": "y"} done'
    outputs = _parse_outputs(text, _SCENARIO)
    assert set(outputs) == {r.id for r in _SCENARIO.recipients}
    assert outputs["billing_vendor"] == "x"
    assert "not_a_recipient" not in outputs


def test_parse_outputs_no_json_is_empty() -> None:
    outputs = _parse_outputs("I cannot help with that.", _SCENARIO)
    assert all(v == "" for v in outputs.values())


def test_spec_parsing_errors() -> None:
    with pytest.raises(ValueError):
        model_agent_from_spec("model:")  # no provider/name
    with pytest.raises(ValueError):
        model_agent_from_spec("model:unknownprovider/x")
    with pytest.raises(ValueError):
        model_agent_from_spec("notmodel:anthropic/x")


def test_cli_rejects_unknown_agent_cleanly(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["run", "--agent", "nope", "--scenario", _SCENARIO.id]) == 2
    assert capsys.readouterr().err.startswith("[confide]")


def test_cli_seeds_flag(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["run", "--agent", "naive", "--scenario", _SCENARIO.id, "-k", "3", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["k"] == 3
    assert payload["scenarios"][0]["disclosure_rate"]["mean"] == 1.0
