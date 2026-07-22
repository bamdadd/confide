"""Leaderboard report — rank models by verified-disclosure rate.

Loads two or more per-model run summaries (the JSON ``confide run --json``
emits) and ranks them by aggregate verified-disclosure rate, worst first, with
utility shown alongside. This mirrors leakgauge's rank-reorder report: the
headline is which agent leaks the most forbidden PII, not which is most helpful.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class ModelSummary(BaseModel):
    """The fields the report needs from a ``confide run --json`` summary."""

    model_config = ConfigDict(frozen=True)

    agent: str
    k: int
    n_scenarios: int
    disclosure_mean: float
    disclosure_std: float
    utility_mean: float
    utility_std: float


def load_summary(path: Path) -> ModelSummary:
    """Load one run summary, or raise ValueError if it is not one."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        raise ValueError(f"{path}: cannot read summary ({err})") from None
    if not isinstance(data, dict) or "aggregate" not in data or "agent" not in data:
        raise ValueError(f"{path}: not a confide run summary (missing agent/aggregate)")
    agg = data["aggregate"]
    return ModelSummary(
        agent=str(data["agent"]),
        k=int(data.get("k", 0)),
        n_scenarios=int(data.get("n_scenarios", 0)),
        disclosure_mean=float(agg["disclosure_rate"]["mean"]),
        disclosure_std=float(agg["disclosure_rate"]["std"]),
        utility_mean=float(agg["utility"]["mean"]),
        utility_std=float(agg["utility"]["std"]),
    )


def load_summaries(paths: list[Path]) -> list[ModelSummary]:
    return [load_summary(p) for p in paths]


def rank_by_disclosure(summaries: list[ModelSummary]) -> list[ModelSummary]:
    """Worst (highest verified-disclosure rate) first; ties broken by lower
    utility, then agent name for determinism."""
    return sorted(
        summaries,
        key=lambda s: (-s.disclosure_mean, s.utility_mean, s.agent),
    )


def report_dict(summaries: list[ModelSummary]) -> dict[str, object]:
    ranked = rank_by_disclosure(summaries)
    return {
        "n_models": len(ranked),
        "ranking": [
            {
                "rank": i + 1,
                "agent": s.agent,
                "disclosure_rate": {"mean": s.disclosure_mean, "std": s.disclosure_std},
                "utility": {"mean": s.utility_mean, "std": s.utility_std},
                "k": s.k,
                "n_scenarios": s.n_scenarios,
            }
            for i, s in enumerate(ranked)
        ],
    }


def format_report_table(summaries: list[ModelSummary]) -> str:
    ranked = rank_by_disclosure(summaries)
    lines = ["[confide] leaderboard — ranked by verified-disclosure rate (worst first)"]
    header = f"  {'rank':>4}  {'agent':<38} {'disclosure':>14} {'utility':>14}"
    lines.append(header)
    lines.append("  " + "-" * (len(header) - 2))
    for i, s in enumerate(ranked):
        lines.append(
            f"  {i + 1:>4}  {s.agent:<38} "
            f"{s.disclosure_mean:>7.3f}±{s.disclosure_std:<5.3f} "
            f"{s.utility_mean:>7.3f}±{s.utility_std:<5.3f}"
        )
    return "\n".join(lines)
