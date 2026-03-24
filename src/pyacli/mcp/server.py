"""MCP server — exposes pyacli library API schemas and Jira operations to Claude."""
from __future__ import annotations

import inspect
import json
import logging
from typing import Any

from pydantic import BaseModel

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from pyacli.lib import dto as dto_module
from pyacli.lib import schemas as schemas_module
from pyacli.lib.client import JiraClient

logger = logging.getLogger(__name__)

server = Server("pyacli")

# Lazy-initialized client (created on first Jira tool call)
_client: JiraClient | None = None


def _get_client() -> JiraClient:
    """Get or create JiraClient from env vars."""
    global _client
    if _client is None:
        _client = JiraClient()
    return _client


# ── Schema helper functions ──────────────────────────


def _get_methods() -> dict[str, dict[str, Any]]:
    """Collect public async method info from JiraClient."""
    methods: dict[str, dict[str, Any]] = {}

    for name, method in inspect.getmembers(JiraClient, predicate=inspect.isfunction):
        if name.startswith("_"):
            continue

        sig = inspect.signature(method)
        doc = inspect.getdoc(method) or ""

        params: dict[str, dict[str, str]] = {}
        for pname, param in sig.parameters.items():
            if pname == "self":
                continue

            annotation = (
                str(param.annotation)
                if param.annotation != inspect.Parameter.empty
                else "Any"
            )
            default = (
                str(param.default)
                if param.default != inspect.Parameter.empty
                else "REQUIRED"
            )
            params[pname] = {"type": annotation, "default": default}

        methods[name] = {"doc": doc, "params": params}

    return methods


def _get_model_schemas() -> dict[str, Any]:
    """Collect JSON schemas from all Pydantic models in dto and schemas modules."""
    result: dict[str, Any] = {}

    for module in [dto_module, schemas_module]:
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if hasattr(obj, "model_json_schema") and obj is not BaseModel:
                result[name] = obj.model_json_schema()

    return result


# ── Tool registration ────────────────────────────────


@server.list_tools()
async def list_tools() -> list[Tool]:
    """Register MCP tools."""
    return [
        # Schema tools
        Tool(
            name="list_methods",
            description="List available JiraClient methods with descriptions",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_method_info",
            description="Get method signature, parameters, and docstring",
            inputSchema={
                "type": "object",
                "properties": {
                    "method_name": {"type": "string"},
                },
                "required": ["method_name"],
            },
        ),
        Tool(
            name="get_models",
            description="Get Pydantic model JSON Schema (all or by name)",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_name": {"type": "string"},
                },
            },
        ),
        # Jira operation tools
        Tool(
            name="list_projects",
            description="List all visible Jira projects",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="list_issue_types",
            description="List available issue types for a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "Project key (uses default if omitted)"},
                },
            },
        ),
        Tool(
            name="get_issue",
            description="Get a single Jira issue by key",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Issue key (e.g., WNVO-110)"},
                },
                "required": ["key"],
            },
        ),
        Tool(
            name="search_issues",
            description="Search Jira issues with JQL",
            inputSchema={
                "type": "object",
                "properties": {
                    "jql": {"type": "string", "description": "JQL query"},
                    "limit": {"type": "integer", "default": 50},
                },
                "required": ["jql"],
            },
        ),
        Tool(
            name="create_issue",
            description="Create a Jira issue under an epic",
            inputSchema={
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "epic": {"type": "string", "description": "Epic name from PYACLI_EPIC_MAP"},
                    "project": {"type": "string", "description": "Project key (uses default if omitted)"},
                    "issue_type": {"type": "string", "default": "Task"},
                    "description": {"type": "string"},
                    "assignee": {"type": "string"},
                    "labels": {"type": "array", "items": {"type": "string"}},
                    "parent": {"type": "string", "description": "Parent issue key (overrides epic)"},
                },
                "required": ["summary"],
            },
        ),
        Tool(
            name="transition_issue",
            description="Change a Jira issue status",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Issue key"},
                    "status": {"type": "string", "description": "Target status name"},
                },
                "required": ["key", "status"],
            },
        ),
    ]


# ── Tool handlers ────────────────────────────────────


async def _handle_schema_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle schema inspection tools."""
    if name == "list_methods":
        methods = _get_methods()
        text = json.dumps(
            {n: m["doc"] for n, m in methods.items()},
            ensure_ascii=False,
            indent=2,
        )
        return [TextContent(type="text", text=text)]

    if name == "get_method_info":
        method_name = arguments["method_name"]
        methods = _get_methods()

        if method_name not in methods:
            return [TextContent(
                type="text",
                text=f"Method '{method_name}' not found. Available: {list(methods.keys())}",
            )]

        text = json.dumps(methods[method_name], ensure_ascii=False, indent=2)
        return [TextContent(type="text", text=text)]

    if name == "get_models":
        schemas = _get_model_schemas()
        model_name = arguments.get("model_name")

        if model_name:
            if model_name not in schemas:
                return [TextContent(
                    type="text",
                    text=f"Model '{model_name}' not found. Available: {list(schemas.keys())}",
                )]
            text = json.dumps(schemas[model_name], ensure_ascii=False, indent=2)
        else:
            text = json.dumps(list(schemas.keys()), ensure_ascii=False, indent=2)

        return [TextContent(type="text", text=text)]

    return []


async def _handle_jira_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle Jira operation tools."""
    client = _get_client()

    if name == "list_projects":
        projects = await client.list_projects()
        data = [{"key": p.key, "name": p.name} for p in projects]
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

    if name == "list_issue_types":
        project = arguments.get("project")
        types = await client.list_issue_types(project=project)
        data = [{"id": t.id, "name": t.name, "subtask": t.subtask} for t in types]
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

    if name == "get_issue":
        issue = await client.get_issue(arguments["key"])
        data = {
            "key": issue.key,
            "summary": issue.summary,
            "status": issue.status.name if issue.status else None,
            "type": issue.issuetype.name if issue.issuetype else None,
            "assignee": issue.assignee.display_name if issue.assignee else None,
            "labels": issue.labels,
            "url": issue.url,
        }
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

    if name == "search_issues":
        issues = await client.search_issues(
            jql=arguments["jql"],
            limit=arguments.get("limit", 50),
        )
        data = [
            {
                "key": i.key,
                "summary": i.summary,
                "status": i.status.name if i.status else None,
                "type": i.issuetype.name if i.issuetype else None,
            }
            for i in issues
        ]
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

    if name == "create_issue":
        issue = await client.create_issue(
            summary=arguments["summary"],
            project=arguments.get("project"),
            epic=arguments.get("epic"),
            description=arguments.get("description"),
            issue_type=arguments.get("issue_type", "Task"),
            assignee=arguments.get("assignee"),
            labels=arguments.get("labels"),
            parent=arguments.get("parent"),
        )
        data = {"key": issue.key, "summary": issue.summary, "url": issue.url}
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

    if name == "transition_issue":
        await client.transition_issue(arguments["key"], status=arguments["status"])
        return [TextContent(type="text", text=f"Transitioned {arguments['key']} to '{arguments['status']}'")]

    return []


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Route tool calls to schema or Jira handlers."""
    schema_tools = {"list_methods", "get_method_info", "get_models"}
    jira_tools = {"list_projects", "list_issue_types", "get_issue", "search_issues", "create_issue", "transition_issue"}

    if name in schema_tools:
        return await _handle_schema_tool(name, arguments)

    if name in jira_tools:
        return await _handle_jira_tool(name, arguments)

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main() -> None:
    """Run MCP server with stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)
