"""Custom exception hierarchy for pyacli."""
from __future__ import annotations


class AcliError(Exception):
    """Base exception for all acli-related errors."""


class AcliNotFoundError(AcliError):
    """Raised when the acli binary is not installed or not found in PATH."""


class AcliAuthError(AcliError):
    """Raised when authentication fails (expired token, missing credentials, etc.)."""


class AcliTimeoutError(AcliError):
    """Raised when an acli command exceeds the configured timeout."""


class AcliValidationError(AcliError):
    """Raised when input validation fails (missing required fields, invalid values)."""
