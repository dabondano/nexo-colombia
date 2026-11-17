"""Controlled vocabularies defined in the master engineering brief.

These are data, not presentation: they are stored with records so that the API,
the UI and the AI layer cannot drop them.
"""

from enum import StrEnum


class EpistemicLabel(StrEnum):
    """Brief section 2.1: every displayed statement belongs to exactly one category."""

    HECHO_DOCUMENTADO = "hecho_documentado"
    INTERPRETACION_JURIDICA = "interpretacion_juridica"
    HIPOTESIS_ANALITICA = "hipotesis_analitica"
    SIMULACION_HIPOTETICA = "simulacion_hipotetica"
    NO_VERIFICADO = "no_verificado"


class ConfidenceClass(StrEnum):
    """Brief section 4.3.3: confidence class of a relationship."""

    VERIFIED_OFFICIAL = "verified_official"
    DECLARED = "declared"
    REPORTED = "reported"
    HISTORICAL = "historical"
    ANALYTICAL_ASSOCIATION = "analytical_association"
    UNVERIFIED_CLAIM = "unverified_claim"


class DataQualityStatus(StrEnum):
    """Rates a record only, never a person or an institution."""

    VERIFIED = "verified"
    ACCEPTABLE = "acceptable"
    INCOMPLETE = "incomplete"
    CONFLICTING = "conflicting"
    STALE = "stale"


class AcquisitionMethod(StrEnum):
    """Brief section 5.2, in order of preference."""

    API = "api"
    OPEN_DATA = "open_data"
    DOWNLOAD = "download"
    RSS = "rss"
    HTML = "html"
    REPOSITORY = "repository"
    PDF_COLLECTION = "pdf_collection"
    UPLOAD = "upload"


class VerificationStatus(StrEnum):
    VERIFIED = "verified"
    NOT_VERIFIED = "not_verified"


class SyncMode(StrEnum):
    INCREMENTAL = "incremental"
    FULL = "full"


class SyncStatus(StrEnum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
