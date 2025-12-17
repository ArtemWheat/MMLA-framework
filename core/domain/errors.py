"""Domain specific exceptions."""

class DomainError(Exception):
    """Base exception for domain level violations."""


class PredictionConsistencyError(DomainError):
    """Raised when required channels or stages are missing."""


class CaseConfigurationError(DomainError):
    """Raised when the case manifest is invalid or incomplete."""
