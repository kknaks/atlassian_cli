"""pyacli — Python async wrapper for Atlassian CLI (acli)."""
from __future__ import annotations

__version__ = "0.0.0"  # Replaced at build time by poetry-dynamic-versioning

from pyacli.lib.client import JiraClient
from pyacli.lib.dto import IssueType, JiraIssue, JiraProject
from pyacli.lib.exceptions import (
    AcliAuthError,
    AcliError,
    AcliNotFoundError,
    AcliTimeoutError,
    AcliValidationError,
)
from pyacli.lib.runner import AcliRunner
from pyacli.lib.schemas import (
    CreateIssueRequest,
    SearchIssuesRequest,
    TransitionIssueRequest,
)

__all__ = [
    "JiraClient",
    "AcliRunner",
    "JiraIssue",
    "JiraProject",
    "IssueType",
    "CreateIssueRequest",
    "SearchIssuesRequest",
    "TransitionIssueRequest",
    "AcliError",
    "AcliAuthError",
    "AcliNotFoundError",
    "AcliTimeoutError",
    "AcliValidationError",
]
