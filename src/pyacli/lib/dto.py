"""Data transfer objects for acli JSON responses."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StatusCategory(BaseModel):
    """Jira status category (e.g., new, indeterminate, done)."""

    model_config = ConfigDict(extra="ignore")

    id: int
    key: str
    name: str
    color_name: str = Field(alias="colorName")


class Status(BaseModel):
    """Jira issue status (e.g., To Do, In Progress, Done)."""

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    status_category: StatusCategory = Field(alias="statusCategory")


class IssueType(BaseModel):
    """Jira issue type (e.g., Task, Epic, Bug)."""

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    subtask: bool = False


class Priority(BaseModel):
    """Jira issue priority (e.g., High, Medium, Low)."""

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str


class User(BaseModel):
    """Jira user reference."""

    model_config = ConfigDict(extra="ignore")

    account_id: str = Field(alias="accountId")
    display_name: str = Field(alias="displayName")
    active: bool = True


class Project(BaseModel):
    """Jira project reference."""

    model_config = ConfigDict(extra="ignore")

    id: str
    key: str
    name: str


class JiraProject(BaseModel):
    """Jira project from acli project list JSON."""

    model_config = ConfigDict(extra="ignore")

    id: str
    key: str
    name: str
    project_type_key: str = Field(default="", alias="projectTypeKey")
    style: str = ""


class ParentRef(BaseModel):
    """Parent issue reference (summary info only)."""

    model_config = ConfigDict(extra="ignore")

    id: str
    key: str
    fields: dict[str, Any] | None = None


class JiraIssue(BaseModel):
    """Jira issue parsed from acli JSON output."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: str
    key: str
    self_url: str = Field(default="", alias="self")

    summary: str = ""
    description: str | None = None
    status: Status | None = None
    issuetype: IssueType | None = None
    priority: Priority | None = None
    assignee: User | None = None
    creator: User | None = None
    reporter: User | None = None
    project: Project | None = None
    labels: list[str] = Field(default_factory=list)
    created: datetime | None = None
    updated: datetime | None = None
    parent: ParentRef | None = None
    duedate: str | None = None
    resolution: dict[str, Any] | None = None

    @classmethod
    def from_acli(cls, data: dict[str, Any]) -> JiraIssue:
        """Parse acli JSON (nested fields structure) into a flat JiraIssue."""
        fields = data.get("fields", {})
        return cls(
            id=data["id"],
            key=data["key"],
            self_url=data.get("self", ""),
            summary=fields.get("summary", ""),
            description=fields.get("description"),
            status=fields.get("status"),
            issuetype=fields.get("issuetype"),
            priority=fields.get("priority"),
            assignee=fields.get("assignee"),
            creator=fields.get("creator"),
            reporter=fields.get("reporter"),
            project=fields.get("project"),
            labels=fields.get("labels", []),
            created=fields.get("created"),
            updated=fields.get("updated"),
            parent=fields.get("parent"),
            duedate=fields.get("duedate"),
            resolution=fields.get("resolution"),
        )

    @property
    def url(self) -> str:
        """Generate browsable issue URL from self_url."""
        if self.self_url and self.key:
            base = self.self_url.split("/rest/")[0]
            return f"{base}/browse/{self.key}"
        return ""
