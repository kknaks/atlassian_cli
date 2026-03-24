"""JiraClient — async wrapper for acli Jira commands."""
from __future__ import annotations

import logging
import os

from pyacli.lib.dto import IssueType, JiraIssue, JiraProject
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
        project: str | None = None,
        epic_map: dict[str, str] | None = None,
        runner: AcliRunner | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.project = project or os.environ.get("PYACLI_DEFAULT_PROJECT", "")
        self._epic_map = epic_map or self._load_epic_map()
        self._runner = runner or AcliRunner(timeout=timeout)

    @staticmethod
    def _load_epic_map() -> dict[str, str]:
        """Load epic map from PYACLI_EPIC_MAP env var.

        Format: "frontend:WNVO-9,backend:WNVO-23,ai:WNVO-24"
        """
        raw = os.environ.get("PYACLI_EPIC_MAP", "")
        if not raw:
            return {}

        result: dict[str, str] = {}
        for pair in raw.split(","):
            pair = pair.strip()
            if ":" not in pair:
                continue
            name, key = pair.split(":", maxsplit=1)
            result[name.strip()] = key.strip()

        return result

    @property
    def epics(self) -> dict[str, str]:
        """Return current epic map (name -> issue key)."""
        return dict(self._epic_map)

    async def list_projects(self) -> list[JiraProject]:
        """List all visible Jira projects."""
        data = await self._runner.run_json(
            "jira", "project", "list", "--paginate", "--json",
        )

        if isinstance(data, list):
            return [JiraProject(**item) for item in data]
        return []

    async def list_issue_types(self, project: str | None = None) -> list[IssueType]:
        """List available issue types for a project via search."""
        target = project or self.project
        if not target:
            raise AcliValidationError(
                "Project is required. Pass project= or set PYACLI_DEFAULT_PROJECT env var."
            )
        data = await self._runner.run_json(
            "jira", "workitem", "search",
            "--jql", f"project = {target}",
            "--limit", "1",
            "--json",
        )

        # Extract unique issue types from project issues
        # More reliable: use get_issue on a known issue to see project types
        # For now, return types from search results
        seen: dict[str, IssueType] = {}
        items = data if isinstance(data, list) else []
        for item in items:
            fields = item.get("fields", {})
            it_data = fields.get("issuetype")
            if it_data and it_data.get("id") not in seen:
                seen[it_data["id"]] = IssueType(**it_data)

        return list(seen.values())

    async def create_issue(
        self,
        summary: str | None = None,
        *,
        project: str | None = None,
        description: str | None = None,
        issue_type: str = "Task",
        assignee: str | None = None,
        labels: list[str] | None = None,
        parent: str | None = None,
        epic: str | None = None,
        request: CreateIssueRequest | None = None,
    ) -> JiraIssue:
        """Create a Jira issue.

        Use epic= to resolve parent from PYACLI_EPIC_MAP.
        Use parent= for explicit parent key. parent takes precedence over epic.
        """
        target_project = project or self.project
        if not target_project:
            raise AcliValidationError(
                "Project is required. Pass project= or set PYACLI_DEFAULT_PROJECT env var."
            )

        # Resolve epic name to parent key
        if parent is None and epic is not None:
            parent = self._epic_map.get(epic)
            if parent is None:
                available = list(self._epic_map.keys())
                raise AcliValidationError(
                    f"Epic '{epic}' not found in epic map. Available: {available}"
                )

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

        args = request.to_acli_args(target_project)
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

    async def add_comment(self, key: str, *, body: str) -> None:
        """Add a comment to an issue."""
        await self._runner.run(
            "jira", "workitem", "comment", "create",
            "--key", key,
            "--body", body,
        )
