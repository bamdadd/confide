"""The unified PII taxonomy: HIPAA Safe-Harbor coverage and domain tagging."""

from __future__ import annotations

from confide.taxonomy import (
    PII_TAXONOMY,
    Domain,
    PIIType,
    hipaa_safe_harbor_types,
    meta_for,
    types_for_domain,
)


def test_every_type_has_metadata() -> None:
    assert set(PII_TAXONOMY) == set(PIIType)


def test_hipaa_safe_harbor_covers_all_eighteen() -> None:
    sh = hipaa_safe_harbor_types()
    assert len(sh) == 18
    indices = [meta_for(t).hipaa_safe_harbor for t in sh]
    assert indices == list(range(1, 19))  # ordered 1..18, no gaps or repeats


def test_financial_only_types_are_not_safe_harbor() -> None:
    # Card / IBAN / CVV etc. are fintech identifiers, not Safe-Harbor classes.
    assert meta_for(PIIType.CARD_NUMBER).hipaa_safe_harbor is None
    assert Domain.FINTECH in meta_for(PIIType.CARD_NUMBER).domains
    assert Domain.HEALTH not in meta_for(PIIType.CARD_NUMBER).domains


def test_shared_types_span_both_domains() -> None:
    for shared in (PIIType.NAME, PIIType.SSN, PIIType.DATE, PIIType.ACCOUNT_NUMBER):
        assert meta_for(shared).domains == frozenset({Domain.HEALTH, Domain.FINTECH})


def test_health_only_types() -> None:
    health = types_for_domain(Domain.HEALTH)
    assert PIIType.MRN in health
    assert PIIType.DIAGNOSIS in health
    assert PIIType.CARD_NUMBER not in health
