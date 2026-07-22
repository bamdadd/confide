"""The leaderboard report: load summaries, rank by verified-disclosure rate."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from confide.cli import main
from confide.report import (
    format_report_table,
    load_summaries,
    rank_by_disclosure,
    report_dict,
)


def _summary(agent: str, disclosure: float, utility: float) -> dict[str, object]:
    return {
        "agent": agent,
        "k": 3,
        "n_scenarios": 4,
        "aggregate": {
            "disclosure_rate": {"mean": disclosure, "std": 0.1},
            "utility": {"mean": utility, "std": 0.0},
        },
        "scenarios": [],
    }


def _write(tmp_path: Path, name: str, payload: dict[str, object]) -> Path:
    p = tmp_path / name
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


def test_ranks_worst_disclosure_first(tmp_path: Path) -> None:
    a = _write(tmp_path, "a.json", _summary("model:x", 0.20, 1.0))
    b = _write(tmp_path, "b.json", _summary("model:y", 0.75, 0.9))
    c = _write(tmp_path, "c.json", _summary("compliant", 0.0, 1.0))
    ranked = rank_by_disclosure(load_summaries([a, b, c]))
    assert [s.agent for s in ranked] == ["model:y", "model:x", "compliant"]


def test_report_dict_and_table(tmp_path: Path) -> None:
    a = _write(tmp_path, "a.json", _summary("model:x", 0.20, 1.0))
    b = _write(tmp_path, "b.json", _summary("model:y", 0.75, 0.9))
    summaries = load_summaries([a, b])
    d = report_dict(summaries)
    assert d["n_models"] == 2
    ranking = d["ranking"]
    assert isinstance(ranking, list)
    assert ranking[0]["agent"] == "model:y"
    assert ranking[0]["rank"] == 1
    assert "verified-disclosure" in format_report_table(summaries)


def test_load_summary_rejects_non_summary(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"hello": "world"}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_summaries([bad])


def test_cli_report_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    a = _write(tmp_path, "a.json", _summary("model:x", 0.20, 1.0))
    b = _write(tmp_path, "b.json", _summary("model:y", 0.75, 0.9))
    assert main(["report", str(a), str(b), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ranking"][0]["agent"] == "model:y"


def test_cli_report_bad_path_exits_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["report", str(tmp_path / "nope.json")]) == 2
    assert capsys.readouterr().err.startswith("[confide]")


def test_cli_run_summary_feeds_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # End-to-end: a real `run --json` summary is a valid report input.
    assert main(["run", "--agent", "naive", "--domain", "health", "--json"]) == 0
    naive = tmp_path / "naive.json"
    naive.write_text(capsys.readouterr().out, encoding="utf-8")
    assert main(["run", "--agent", "compliant", "--domain", "health", "--json"]) == 0
    compliant = tmp_path / "compliant.json"
    compliant.write_text(capsys.readouterr().out, encoding="utf-8")

    assert main(["report", str(naive), str(compliant), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ranking"][0]["agent"] == "naive"  # naive leaks most
    assert payload["ranking"][-1]["agent"] == "compliant"
