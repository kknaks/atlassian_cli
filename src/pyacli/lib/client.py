"""JiraClient — async wrapper for acli Jira commands."""
from __future__ import annotations

import logging

from pyacli.lib.dto import JiraIssue
from pyacli.lib.exceptions import AcliValidationError
from pyacli.lib.runner import AcliRunner
from pyacli.lib.schemas import (
    CreateIssueRequest,
    SearchIssuesRequest,
    TransitionIssueRequest,
)

logger = logging.getLogger(__name__)


class JiraClient:
    """Async client for Jira operations via acli CLI."""

    def __init__(
        self,
        project: str,
        runner: AcliRunner | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.project = project
        self._runner = runner or AcliRunner(timeout=timeout)

    async def create_issue(
        self,
        summary: str | None = None,
        *,
        description: str | None = None,
        issue_type: str = "Task",
        assignee: str | None = None,
        labels: list[str] | None = None,
        parent: str | None = None,
        request: CreateIssueRequest | None = None,
    ) -> JiraIssue:
        """Create a Jira issue. Pass keyword args or a CreateIssueRequest."""
        if request is None:
            if summary is None:
                raise AcliValidationError(
                    "Either 'summary' or 'request' is required."
                )
            request = CreateIssueRequest(
                summary=summary,
                description=description,
                type=issue_type,
                assignee=assignee,
                labels=labels or [],
                parent=parent,
            )

        args = request.to_acli_args(self.project)
        logger.debug("create_issue args: %s", args)

        data = await self._runner.run_json(*args)
        return JiraIssue.from_acli(data)

    async def get_issue(self, key: str) -> JiraIssue:
        """Get a single issue by key."""
        data = await self._runner.run_json(
            "jira", "workitem", "view", key, "--json",
        )
        return JiraIssue.from_acli(data)

    async def search_issues(
        self,
        jql: str | None = None,
        *,
        limit: int = 50,
        fields: str | None = None,
        request: SearchIssuesRequest | None = None,
    ) -> list[JiraIssue]:
        """Search issues with JQL. Pass keyword args or a SearchIssuesRequest."""
        if request is None:
            if jql is None:
                raise AcliValidationError(
                    "Either 'jql' or 'request' is required."
                )
            request = SearchIssuesRequest(jql=jql, limit=limit, fields=fields)

        args = request.to_acli_args()
        logger.debug("search_issues args: %s", args)

        data = await self._runner.run_json(*args)

        if isinstance(data, list):
            return [JiraIssue.from_acli(item) for item in data]
        return []

    async def transition_issue(
        self,
        key: str,
        *,
        status: str,
    ) -> None:
        """Transition an issue to a new status."""
        request = TransitionIssueRequest(key=key, status=status)
        args = request.to_acli_args()
        logger.debug("transition_issue args: %s", args)

        await self._runner.run(*args)
