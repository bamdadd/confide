"""The unified PII taxonomy — the spine both domain packs share.

Covers the **HIPAA Safe-Harbor 18** identifier classes (45 CFR 164.514(b)(2))
for the health domain and the **core financial PII** classes for fintech, in one
enum so a single scorer and a single appropriateness matrix span both domains.
Several classes (names, dates, geographic subdivisions, account numbers, SSN /
tax id) are shared across domains — the taxonomy marks that explicitly rather
than duplicating them.

Nothing here is data about a person: this module is the *schema* of identifier
kinds. All concrete values live in the synthetic scenario packs.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class Domain(StrEnum):
    """The regulated domain a scenario (and an identifier's relevance) lives in."""

    HEALTH = "health"
    FINTECH = "fintech"


class PIICategory(StrEnum):
    """A coarse grouping of identifier kinds, for reporting and filtering."""

    IDENTITY = "identity"
    CONTACT = "contact"
    GEO = "geo"
    TEMPORAL = "temporal"
    HEALTH = "health"
    FINANCIAL = "financial"
    DEVICE = "device"
    CREDENTIAL = "credential"
    BIOMETRIC = "biometric"
    OTHER = "other"


class PIIType(StrEnum):
    """A kind of personally identifying attribute.

    The first 18 members map onto the HIPAA Safe-Harbor identifier classes; the
    remaining members are the core financial identifiers fintech workflows turn
    on. Shared classes (e.g. :attr:`ACCOUNT_NUMBER`, :attr:`SSN`) are listed once
    and tagged for both domains in :data:`PII_TAXONOMY`.
    """

    # --- HIPAA Safe-Harbor 18 --------------------------------------------------
    NAME = "name"  # 1. names
    GEO_SUBDIVISION = "geo_subdivision"  # 2. geography smaller than a state
    DATE = "date"  # 3. dates (except year) tied to an individual
    PHONE = "phone"  # 4. telephone numbers
    FAX = "fax"  # 5. fax numbers
    EMAIL = "email"  # 6. email addresses
    SSN = "ssn"  # 7. social security numbers
    MRN = "mrn"  # 8. medical record numbers
    HEALTH_PLAN_ID = "health_plan_id"  # 9. health plan beneficiary numbers
    ACCOUNT_NUMBER = "account_number"  # 10. account numbers
    LICENSE_NUMBER = "license_number"  # 11. certificate / license numbers
    VEHICLE_ID = "vehicle_id"  # 12. vehicle identifiers / plates
    DEVICE_ID = "device_id"  # 13. device identifiers / serial numbers
    URL = "url"  # 14. web URLs
    IP_ADDRESS = "ip_address"  # 15. IP addresses
    BIOMETRIC_ID = "biometric_id"  # 16. biometric identifiers
    FULL_FACE_PHOTO = "full_face_photo"  # 17. full-face photos / comparable images
    OTHER_UNIQUE_ID = "other_unique_id"  # 18. any other unique identifying code

    # --- core financial PII ----------------------------------------------------
    CARD_NUMBER = "card_number"  # primary account number (PAN)
    IBAN = "iban"  # international bank account number
    ROUTING_NUMBER = "routing_number"  # routing / sort code
    CARD_SECURITY = "card_security"  # expiry / CVV
    ACCOUNT_BALANCE = "account_balance"  # balance / holdings
    TRANSACTION = "transaction"  # a specific transaction detail
    CREDIT_SCORE = "credit_score"  # credit score / rating
    TAX_ID = "tax_id"  # taxpayer identification number

    # A clinical fact that is itself identifying-in-context (diagnosis code,
    # medication). Not a Safe-Harbor *identifier* class, but the disclosure a
    # health agent most often mishandles, so the taxonomy carries it explicitly.
    DIAGNOSIS = "diagnosis"


class PIIMeta(BaseModel):
    """Static metadata for one :class:`PIIType`."""

    model_config = ConfigDict(frozen=True)

    label: str
    category: PIICategory
    domains: frozenset[Domain]
    # HIPAA Safe-Harbor identifier index (1-18), or None if not a Safe-Harbor
    # class (e.g. the financial-only identifiers and DIAGNOSIS).
    hipaa_safe_harbor: int | None = None


_BOTH = frozenset({Domain.HEALTH, Domain.FINTECH})
_HEALTH = frozenset({Domain.HEALTH})
_FINTECH = frozenset({Domain.FINTECH})


PII_TAXONOMY: dict[PIIType, PIIMeta] = {
    PIIType.NAME: PIIMeta(
        label="Name", category=PIICategory.IDENTITY, domains=_BOTH, hipaa_safe_harbor=1
    ),
    PIIType.GEO_SUBDIVISION: PIIMeta(
        label="Geographic subdivision", category=PIICategory.GEO, domains=_BOTH, hipaa_safe_harbor=2
    ),
    PIIType.DATE: PIIMeta(
        label="Date tied to an individual",
        category=PIICategory.TEMPORAL,
        domains=_BOTH,
        hipaa_safe_harbor=3,
    ),
    PIIType.PHONE: PIIMeta(
        label="Telephone number", category=PIICategory.CONTACT, domains=_BOTH, hipaa_safe_harbor=4
    ),
    PIIType.FAX: PIIMeta(
        label="Fax number", category=PIICategory.CONTACT, domains=_BOTH, hipaa_safe_harbor=5
    ),
    PIIType.EMAIL: PIIMeta(
        label="Email address", category=PIICategory.CONTACT, domains=_BOTH, hipaa_safe_harbor=6
    ),
    PIIType.SSN: PIIMeta(
        label="Social Security number",
        category=PIICategory.IDENTITY,
        domains=_BOTH,
        hipaa_safe_harbor=7,
    ),
    PIIType.MRN: PIIMeta(
        label="Medical record number",
        category=PIICategory.HEALTH,
        domains=_HEALTH,
        hipaa_safe_harbor=8,
    ),
    PIIType.HEALTH_PLAN_ID: PIIMeta(
        label="Health plan beneficiary number",
        category=PIICategory.HEALTH,
        domains=_HEALTH,
        hipaa_safe_harbor=9,
    ),
    PIIType.ACCOUNT_NUMBER: PIIMeta(
        label="Account number", category=PIICategory.FINANCIAL, domains=_BOTH, hipaa_safe_harbor=10
    ),
    PIIType.LICENSE_NUMBER: PIIMeta(
        label="Certificate / license number",
        category=PIICategory.CREDENTIAL,
        domains=_BOTH,
        hipaa_safe_harbor=11,
    ),
    PIIType.VEHICLE_ID: PIIMeta(
        label="Vehicle identifier", category=PIICategory.DEVICE, domains=_BOTH, hipaa_safe_harbor=12
    ),
    PIIType.DEVICE_ID: PIIMeta(
        label="Device identifier / serial number",
        category=PIICategory.DEVICE,
        domains=_BOTH,
        hipaa_safe_harbor=13,
    ),
    PIIType.URL: PIIMeta(
        label="Web URL", category=PIICategory.CONTACT, domains=_BOTH, hipaa_safe_harbor=14
    ),
    PIIType.IP_ADDRESS: PIIMeta(
        label="IP address", category=PIICategory.DEVICE, domains=_BOTH, hipaa_safe_harbor=15
    ),
    PIIType.BIOMETRIC_ID: PIIMeta(
        label="Biometric identifier",
        category=PIICategory.BIOMETRIC,
        domains=_BOTH,
        hipaa_safe_harbor=16,
    ),
    PIIType.FULL_FACE_PHOTO: PIIMeta(
        label="Full-face photograph",
        category=PIICategory.BIOMETRIC,
        domains=_BOTH,
        hipaa_safe_harbor=17,
    ),
    PIIType.OTHER_UNIQUE_ID: PIIMeta(
        label="Other unique identifying code",
        category=PIICategory.OTHER,
        domains=_BOTH,
        hipaa_safe_harbor=18,
    ),
    PIIType.CARD_NUMBER: PIIMeta(
        label="Card number (PAN)", category=PIICategory.FINANCIAL, domains=_FINTECH
    ),
    PIIType.IBAN: PIIMeta(label="IBAN", category=PIICategory.FINANCIAL, domains=_FINTECH),
    PIIType.ROUTING_NUMBER: PIIMeta(
        label="Routing / sort code", category=PIICategory.FINANCIAL, domains=_FINTECH
    ),
    PIIType.CARD_SECURITY: PIIMeta(
        label="Card expiry / CVV", category=PIICategory.FINANCIAL, domains=_FINTECH
    ),
    PIIType.ACCOUNT_BALANCE: PIIMeta(
        label="Account balance", category=PIICategory.FINANCIAL, domains=_FINTECH
    ),
    PIIType.TRANSACTION: PIIMeta(
        label="Transaction detail", category=PIICategory.FINANCIAL, domains=_FINTECH
    ),
    PIIType.CREDIT_SCORE: PIIMeta(
        label="Credit score", category=PIICategory.FINANCIAL, domains=_FINTECH
    ),
    PIIType.TAX_ID: PIIMeta(
        label="Taxpayer identification number", category=PIICategory.IDENTITY, domains=_BOTH
    ),
    PIIType.DIAGNOSIS: PIIMeta(
        label="Diagnosis / clinical fact", category=PIICategory.HEALTH, domains=_HEALTH
    ),
}


def meta_for(pii_type: PIIType) -> PIIMeta:
    """Return the taxonomy metadata for ``pii_type`` (raises if unregistered)."""
    return PII_TAXONOMY[pii_type]


def types_for_domain(domain: Domain) -> list[PIIType]:
    """All identifier kinds relevant to ``domain``, in enum order."""
    return [t for t in PIIType if domain in PII_TAXONOMY[t].domains]


def hipaa_safe_harbor_types() -> list[PIIType]:
    """The 18 HIPAA Safe-Harbor identifier classes, ordered 1-18."""
    return sorted(
        (t for t, m in PII_TAXONOMY.items() if m.hipaa_safe_harbor is not None),
        key=lambda t: PII_TAXONOMY[t].hipaa_safe_harbor or 0,
    )
