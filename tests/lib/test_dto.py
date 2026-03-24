"""Tests for DTO models (acli JSON response parsing)."""
from __future__ import annotations

import pytest

from pyacli.lib.dto import (
    IssueType,
    JiraIssue,
    ParentRef,
    Priority,
    Project,
    Status,
    StatusCategory,
    User,
)


class TestSubModels:
    """Tests for nested DTO models."""

    def test_status_category_alias(self) -> None:
        data = {"id": 2, "key": "new", "name": "To Do", "colorName": "blue-gray"}
        sc = StatusCategory(**data)
        assert sc.color_name == "blue-gray"

    def test_status_with_category(self) -> None:
        data = {
            "id": "10000",
            "name": "해야 할 일",
            "statusCategory": {
                "id": 2, "key": "new", "name": "해야 할 일", "colorName": "blue-gray",
            },
        }
        status = Status(**data)
        assert status.name == "해야 할 일"
        assert status.status_category.key == "new"

    def test_issue_type(self) -> None:
        it = IssueType(id="10003", name="하위 작업", subtask=True)
        assert it.subtask is True

    def test_issue_type_default_subtask(self) -> None:
        it = IssueType(id="10001", name="Task")
        assert it.subtask is False

    def test_priority(self) -> None:
        p = Priority(id="3", name="Medium")
        assert p.name == "Medium"

    def test_user_alias(self) -> None:
        data = {"accountId": "abc123", "displayName": "홍길동", "active": True}
        user = User(**data)
        assert user.account_id == "abc123"
        assert user.display_name == "홍길동"

    def test_project(self) -> None:
        p = Project(id="10000", key="WNVO", name="멋사로켓단")
        assert p.key == "WNVO"

    def test_parent_ref(self) -> None:
        data = {"id": "10155", "key": "WNVO-106", "fields": {"summary": "적성검사"}}
        parent = ParentRef(**data)
        assert parent.key == "WNVO-106"

    def test_extra_fields_ignored(self) -> None:
        """Extra fields in acli response should be silently ignored."""
        data = {
            "id": "3", "name": "Medium",
            "iconUrl": "https://example.com/icon.svg",
            "self": "https://example.com/api",
        }
        p = Priority(**data)
        assert p.name == "Medium"


class TestJiraIssue:
    """Tests for JiraIssue model."""

    def test_from_acli(self, sample_issue_json: dict) -> None:
        issue = JiraIssue.from_acli(sample_issue_json)

        assert issue.key == "WNVO-110"
        assert issue.id == "10163"
        assert issue.summary == "적성검사 결과 렌더링"
        assert issue.description is None
        assert issue.status is not None
        assert issue.status.name == "해야 할 일"
        assert issue.issuetype is not None
        assert issue.issuetype.name == "하위 작업"
        assert issue.priority is not None
        assert issue.priority.name == "Medium"
        assert issue.creator is not None
        assert issue.creator.display_name == "강진수"
        assert issue.project is not None
        assert issue.project.key == "WNVO"
        assert issue.labels == []
        assert issue.assignee is None
        assert issue.parent is None

    def test_from_acli_minimal(self) -> None:
        """Minimal JSON with only required top-level fields."""
        data = {"id": "1", "key": "TEST-1", "fields": {}}
        issue = JiraIssue.from_acli(data)

        assert issue.key == "TEST-1"
        assert issue.summary == ""
        assert issue.status is None
        assert issue.labels == []

    def test_from_acli_no_fields_key(self) -> None:
        """JSON without fields key should still parse."""
        data = {"id": "1", "key": "TEST-1"}
        issue = JiraIssue.from_acli(data)

        assert issue.key == "TEST-1"
        assert issue.summary == ""

    def test_url_property(self, sample_issue_json: dict) -> None:
        issue = JiraIssue.from_acli(sample_issue_json)
        assert issue.url == "https://jira-prod-ap-31-2.prod.atl-paas.net/browse/WNVO-110"

    def test_url_property_empty(self) -> None:
        data = {"id": "1", "key": "TEST-1", "fields": {}}
        issue = JiraIssue.from_acli(data)
        assert issue.url == ""

    def test_created_datetime_parsing(self, sample_issue_json: dict) -> None:
        issue = JiraIssue.from_acli(sample_issue_json)
        assert issue.created is not None
        assert issue.created.year == 2025
        assert issue.created.month == 7
