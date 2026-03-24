"""Input schemas for pyacli library calls."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CreateIssueRequest(BaseModel):
    """Input schema for create_issue()."""

    model_config = ConfigDict(extra="forbid")

    summary: str
    description: str | None = None
    issue_type: str = Field(default="Task", alias="type")
    assignee: str | None = None
    labels: list[str] = Field(default_factory=list)
    parent: str | None = None

    def to_acli_args(self, project: str) -> list[str]:
        """Convert to acli CLI argument list."""
        args = [
            "jira", "workitem", "create",
            "--project", project,
            "--type", self.issue_type,
            "--summary", self.summary,
            "--json",
        ]
        if self.description:
            args.extend(["--description", self.description])
        if self.assignee:
            args.extend(["--assignee", self.assignee])
        if self.labels:
            args.extend(["--label", ",".join(self.labels)])
        if self.parent:
            args.extend(["--parent", self.parent])
        return args


class SearchIssuesRequest(BaseModel):
    """Input schema for search_issues()."""

    model_config = ConfigDict(extra="forbid")

    jql: str
    limit: int = 50
    fields: str | None = None

    def to_acli_args(self) -> list[str]:
        """Convert to acli CLI argument list."""
        args = [
            "jira", "workitem", "search",
            "--jql", self.jql,
            "--limit", str(self.limit),
            "--json",
        ]
        if self.fields:
            args.extend(["--fields", self.fields])
        return args


class TransitionIssueRequest(BaseModel):
    """Input schema for transition_issue()."""

    model_config = ConfigDict(extra="forbid")

    key: str
    status: str

    def to_acli_args(self) -> list[str]:
        """Convert to acli CLI argument list."""
        return [
            "jira", "workitem", "transition",
            "--key", self.key,
            "--status", self.status,
            "--yes",
            "--json",
        ]
