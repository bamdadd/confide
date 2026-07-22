"""The CLI: list-scenarios, run, json, and clean error handling."""

from __future__ import annotations

import json

import pytest

from confide.cli import main


def test_list_scenarios(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--list-scenarios"]) == 0
    out = capsys.readouterr().out
    assert "health-discharge-handoff" in out
    assert "fintech-loan-underwriting" in out


def test_run_default_naive(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["run"]) == 0
    out = capsys.readouterr().out
    assert "verified-disclosure rate" in out


def test_run_json_is_machine_readable(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["run", "--domain", "fintech", "--agent", "compliant", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["agent"] == "compliant"
    assert payload["aggregate"]["disclosure_rate"] == 0.0
    assert {s["scenario_id"] for s in payload["scenarios"]} == {
        "fintech-loan-underwriting",
        "fintech-support-dispute",
    }


def test_run_single_scenario(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["run", "--scenario", "health-discharge-handoff", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["n_scenarios"] == 1
    assert payload["scenarios"][0]["disclosure_rate"] == 1.0  # naive default


def test_unknown_scenario_errors_cleanly(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["run", "--scenario", "nope"]) == 2
    err = capsys.readouterr().err
    assert err.startswith("[confide]")
    assert "Traceback" not in err
