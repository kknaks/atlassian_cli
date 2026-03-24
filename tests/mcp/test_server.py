"""Tests for MCP server tools."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pyacli.lib.dto import IssueType, JiraIssue, JiraProject
from pyacli.lib.runner import AcliResult
from pyacli.mcp.server import call_tool, list_tools


class TestListTools:
    """Tests for MCP tool registration."""

    async def test_returns_eleven_tools(self) -> None:
        tools = await list_tools()
        assert len(tools) == 11

    async def test_schema_tool_names(self) -> None:
        tools = await list_tools()
        names = {t.name for t in tools}
        assert {"list_methods", "get_method_info", "get_models"}.issubset(names)

    async def test_jira_tool_names(self) -> None:
        tools = await list_tools()
        names = {t.name for t in tools}
        assert {"list_projects", "list_issue_types", "get_issue", "search_issues", "create_issue", "transition_issue"}.issubset(names)


class TestCallToolListMethods:
    """Tests for list_methods tool."""

    async def test_returns_methods(self) -> None:
        result = await call_tool("list_methods", {})
        assert len(result) == 1

        data = json.loads(result[0].text)
        assert "create_issue" in data
        assert "get_issue" in data
        assert "search_issues" in data
        assert "transition_issue" in data


class TestCallToolGetMethodInfo:
    """Tests for get_method_info tool."""

    async def test_existing_method(self) -> None:
        result = await call_tool("get_method_info", {"method_name": "create_issue"})
        data = json.loads(result[0].text)

        assert "doc" in data
        assert "params" in data
        assert "summary" in data["params"]

    async def test_nonexistent_method(self) -> None:
        result = await call_tool("get_method_info", {"method_name": "does_not_exist"})
        assert "not found" in result[0].text


class TestCallToolGetModels:
    """Tests for get_models tool."""

    async def test_list_all_models(self) -> None:
        result = await call_tool("get_models", {})
        data = json.loads(result[0].text)

        assert isinstance(data, list)
        assert "JiraIssue" in data
        assert "CreateIssueRequest" in data

    async def test_specific_model(self) -> None:
        result = await call_tool("get_models", {"model_name": "JiraIssue"})
        data = json.loads(result[0].text)

        assert "properties" in data
        assert "title" in data

    async def test_nonexistent_model(self) -> None:
        result = await call_tool("get_models", {"model_name": "FakeModel"})
        assert "not found" in result[0].text


class TestJiraTools:
    """Tests for Jira operation tools (mocked client)."""

    @patch("pyacli.mcp.server._get_client")
    async def test_list_projects(self, mock_get: MagicMock) -> None:
        client = MagicMock()
        client.list_projects = AsyncMock(return_value=[
            JiraProject(id="1", key="WNVO", name="멋사로켓단"),
        ])
        mock_get.return_value = client

        result = await call_tool("list_projects", {})
        data = json.loads(result[0].text)

        assert len(data) == 1
        assert data[0]["key"] == "WNVO"

    @patch("pyacli.mcp.server._get_client")
    async def test_list_issue_types(self, mock_get: MagicMock) -> None:
        client = MagicMock()
        client.list_issue_types = AsyncMock(return_value=[
            IssueType(id="1", name="작업", subtask=False),
            IssueType(id="2", name="버그", subtask=False),
        ])
        mock_get.return_value = client

        result = await call_tool("list_issue_types", {"project": "WNVO"})
        data = json.loads(result[0].text)

        assert len(data) == 2
        names = [d["name"] for d in data]
        assert "작업" in names
        assert "버그" in names

    @patch("pyacli.mcp.server._get_client")
    async def test_get_issue(self, mock_get: MagicMock) -> None:
        issue = JiraIssue(id="1", key="WNVO-110", summary="테스트")
        client = MagicMock()
        client.get_issue = AsyncMock(return_value=issue)
        mock_get.return_value = client

        result = await call_tool("get_issue", {"key": "WNVO-110"})
        data = json.loads(result[0].text)

        assert data["key"] == "WNVO-110"
        assert data["summary"] == "테스트"

    @patch("pyacli.mcp.server._get_client")
    async def test_search_issues(self, mock_get: MagicMock) -> None:
        issues = [
            JiraIssue(id="1", key="WNVO-1", summary="이슈1"),
            JiraIssue(id="2", key="WNVO-2", summary="이슈2"),
        ]
        client = MagicMock()
        client.search_issues = AsyncMock(return_value=issues)
        mock_get.return_value = client

        result = await call_tool("search_issues", {"jql": "project = WNVO"})
        data = json.loads(result[0].text)

        assert len(data) == 2

    @patch("pyacli.mcp.server._get_client")
    async def test_create_issue(self, mock_get: MagicMock) -> None:
        issue = JiraIssue(id="1", key="WNVO-112", summary="새 이슈")
        client = MagicMock()
        client.create_issue = AsyncMock(return_value=issue)
        mock_get.return_value = client

        result = await call_tool("create_issue", {
            "summary": "새 이슈",
            "epic": "frontend",
        })
        data = json.loads(result[0].text)

        assert data["key"] == "WNVO-112"

    @patch("pyacli.mcp.server._get_client")
    async def test_transition_issue(self, mock_get: MagicMock) -> None:
        client = MagicMock()
        client.transition_issue = AsyncMock(return_value=None)
        mock_get.return_value = client

        result = await call_tool("transition_issue", {"key": "WNVO-110", "status": "완료"})

        assert "완료" in result[0].text
        client.transition_issue.assert_awaited_once_with("WNVO-110", status="완료")


    @patch("pyacli.mcp.server._get_client")
    async def test_add_comment(self, mock_get: MagicMock) -> None:
        client = MagicMock()
        client.add_comment = AsyncMock(return_value=None)
        mock_get.return_value = client

        result = await call_tool("add_comment", {"key": "WNVO-110", "body": "traceback log"})

        assert "WNVO-110" in result[0].text
        client.add_comment.assert_awaited_once_with("WNVO-110", body="traceback log")

    @patch("pyacli.mcp.server._get_client")
    async def test_list_comments(self, mock_get: MagicMock) -> None:
        client = MagicMock()
        client.list_comments = AsyncMock(return_value=[
            {"author": "user", "body": "comment", "id": "1"},
        ])
        mock_get.return_value = client

        result = await call_tool("list_comments", {"key": "WNVO-110"})
        data = json.loads(result[0].text)

        assert len(data) == 1
        assert data[0]["body"] == "comment"


class TestUnknownTool:
    """Tests for unknown tool handling."""

    async def test_unknown_tool(self) -> None:
        result = await call_tool("unknown_tool", {})
        assert "Unknown tool" in result[0].text
