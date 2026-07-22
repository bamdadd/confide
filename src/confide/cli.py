"""confide CLI — list scenarios and run the deterministic scorer offline.

    confide --list-scenarios
    confide run [--scenario <id>] [--domain health|fintech] [--agent naive|compliant] [--json]

``run`` scores a reference agent (no API key, no model) over the selected
synthetic scenarios and prints per-scenario disclosure-rate / utility plus an
aggregate. ``--json`` emits the same result as machine-readable JSON. Errors on
bad input print a clean ``[confide] ...`` message and exit 2.
"""

from __future__ import annotations

import argparse
import json
import sys

from confide.reference import DEFAULT_AGENT, REFERENCE_AGENTS, reference_agent
from confide.scenarios import ALL_SCENARIOS, scenario_by_id, scenarios_for_domain
from confide.scoring import score
from confide.taxonomy import Domain
from confide.types import Scenario, ScoreResult


def _select(args: argparse.Namespace) -> list[Scenario]:
    if args.scenario is not None:
        return [scenario_by_id(args.scenario)]
    if args.domain is not None:
        return scenarios_for_domain(Domain(args.domain))
    return list(ALL_SCENARIOS)


def _list_scenarios() -> int:
    print("[confide] synthetic scenario packs (all data invented)")
    header = f"  {'scenario_id':<30} {'domain':<8} {'forbidden':>9} {'appropriate':>11}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for s in ALL_SCENARIOS:
        print(f"  {s.id:<30} {s.domain:<8} {len(s.forbidden):>9} {len(s.appropriate_flows):>11}")
    return 0


def _result_dict(scenario: Scenario, result: ScoreResult) -> dict[str, object]:
    return {
        "scenario_id": scenario.id,
        "domain": str(scenario.domain),
        "disclosure_rate": result.disclosure_rate,
        "utility": result.utility,
        "violations": [list(f) for f in result.violations],
        "appropriate": [list(f) for f in result.appropriate],
    }


def _run(args: argparse.Namespace) -> int:
    scenarios = _select(args)
    agent = reference_agent(args.agent)
    results = [(s, score(agent(s), s)) for s in scenarios]

    n = len(results)
    mean_disclosure = sum(r.disclosure_rate for _, r in results) / n if n else 0.0
    mean_utility = sum(r.utility for _, r in results) / n if n else 0.0

    if args.json:
        payload = {
            "agent": args.agent,
            "n_scenarios": n,
            "aggregate": {"disclosure_rate": mean_disclosure, "utility": mean_utility},
            "scenarios": [_result_dict(s, r) for s, r in results],
        }
        print(json.dumps(payload, indent=2))
        return 0

    print(f"[confide] agent={args.agent} scenarios={n}")
    header = f"  {'scenario_id':<30} {'domain':<8} {'disclosure':>11} {'utility':>8}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for s, r in results:
        print(f"  {s.id:<30} {s.domain:<8} {r.disclosure_rate:>11.3f} {r.utility:>8.3f}")
    print("")
    print(f"  aggregate over {n} scenario(s):")
    print(f"    verified-disclosure rate : {mean_disclosure:.3f}")
    print(f"    utility                  : {mean_utility:.3f}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="confide")
    parser.add_argument(
        "--list-scenarios", action="store_true", help="list the synthetic scenario packs and exit"
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=["run"],
        help="what to do (default: run)",
    )
    parser.add_argument("--scenario", help="run a single scenario by id")
    parser.add_argument(
        "--domain", choices=[str(d) for d in Domain], help="restrict to one domain pack"
    )
    parser.add_argument(
        "--agent",
        default=DEFAULT_AGENT,
        choices=sorted(REFERENCE_AGENTS),
        help=f"reference agent to score (default: {DEFAULT_AGENT})",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.list_scenarios:
        return _list_scenarios()
    try:
        return _run(args)
    except ValueError as err:
        print(f"[confide] {err}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
