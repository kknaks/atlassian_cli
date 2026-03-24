"""Tests for MCP server tools."""
from __future__ import annotations

import json

import pytest

from pyacli.mcp.server import call_tool, list_tools


class TestListTools:
    """Tests for MCP tool registration."""

    async def test_returns_three_tools(self) -> None:
        tools = await list_tools()
        assert len(tools) == 3

    async def test_tool_names(self) -> None:
        tools = await list_tools()
        names = {t.name for t in tools}
        assert names == {"list_methods", "get_method_info", "get_models"}


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


class TestUnknownTool:
    """Tests for unknown tool handling."""

    async def test_unknown_tool(self) -> None:
        result = await call_tool("unknown_tool", {})
        assert "Unknown tool" in result[0].text
