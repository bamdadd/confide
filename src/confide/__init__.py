"""confide — a domain-specialized privacy / contextual-integrity leakage benchmark.

Measures whether a domain agent (health, fintech) discloses a *forbidden* PII
attribute to a *forbidden* recipient given the task context. Scoring is
deterministic and verified — never an LLM judge.

All scenario data in this package is SYNTHETIC and invented. See the README's
"Synthetic by design" note and docs/THREAT_MODEL.md.
"""

from __future__ import annotations

__version__ = "0.0.1"
