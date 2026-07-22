"""Deterministic reference agents for the offline ``confide run`` path.

These stand in for a model so the benchmark is runnable with no API key, exactly
as leakgauge's stub adapter does. They are not models — each is a fixed policy
that maps a scenario to the text addressed to each recipient:

- ``naive`` — a helpful-but-careless agent that hands every recipient every
  attribute it holds. It completes the task (full utility) but discloses PII
  indiscriminately, so it exercises the forbidden matrix (high disclosure rate).
- ``compliant`` — an agent that discloses an attribute to a recipient only on an
  appropriate flow. Full utility, zero verified disclosure — the ceiling.

Real evaluation swaps these for a model's per-recipient outputs; the scorer is
identical either way.
"""

from __future__ import annotations

from collections.abc import Callable

from confide.types import Scenario

# A reference agent maps a scenario to {recipient_id: text addressed to them}.
ReferenceAgent = Callable[[Scenario], dict[str, str]]


def naive_agent(scenario: Scenario) -> dict[str, str]:
    """Hand every recipient every attribute value — careless over-sharing."""
    all_values = " ; ".join(a.value for a in scenario.attributes)
    return {r.id: all_values for r in scenario.recipients}


def compliant_agent(scenario: Scenario) -> dict[str, str]:
    """Disclose an attribute to a recipient only where the flow is appropriate."""
    value_by_name = {a.name: a.value for a in scenario.attributes}
    outputs: dict[str, list[str]] = {r.id: [] for r in scenario.recipients}
    for attribute_name, recipient_id in scenario.appropriate_flows:
        outputs[recipient_id].append(value_by_name[attribute_name])
    return {rid: " ; ".join(parts) for rid, parts in outputs.items()}


REFERENCE_AGENTS: dict[str, ReferenceAgent] = {
    "naive": naive_agent,
    "compliant": compliant_agent,
}
DEFAULT_AGENT = "naive"


def reference_agent(name: str) -> ReferenceAgent:
    """Look up a reference agent by name, or raise ValueError."""
    try:
        return REFERENCE_AGENTS[name]
    except KeyError:
        raise ValueError(
            f"unknown reference agent {name!r}; choose from {sorted(REFERENCE_AGENTS)}"
        ) from None
