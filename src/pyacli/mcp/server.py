"""MCP server — exposes pyacli library API schemas to Claude."""
from __future__ import annotations

import inspect
import json
import logging
from typing import Any

from pydantic import BaseModel

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from pyacli.lib import client as client_module
from pyacli.lib import dto as dto_module
from pyacli.lib import schemas as schemas_module
from pyacli.lib.client import JiraClient

logger = logging.getLogger(__name__)

server = Server("pyacli")


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


@server.list_tools()
async def list_tools() -> list[Tool]:
    """Register MCP tools."""
    return [
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
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle MCP tool calls."""
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

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main() -> None:
    """Run MCP server with stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)
