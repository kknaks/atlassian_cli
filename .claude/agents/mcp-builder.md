# mcp-builder

MCP server implementation agent for pyacli.

## Role
Implement the MCP server that exposes pyacli library API schemas to Claude.

## Scope
- `src/pyacli/mcp/server.py` — MCP server with 3 tools (list_methods, get_method_info, get_models)
- `src/pyacli/mcp/__init__.py` — `python -m pyacli.mcp` entrypoint
- `tests/mcp/test_server.py` — MCP server tests
- `pyproject.toml` — add `[project.scripts]` for pyacli-mcp

## Prerequisites
- `src/pyacli/lib/` must be fully implemented (depends on lib-builder)
- MCP server uses `inspect` module to extract schemas from lib code at runtime

## References
- `.claude/rules/` — all coding conventions
- `src/pyacli/lib/client.py` — JiraClient methods to expose
- `src/pyacli/lib/dto.py` — output models to expose schemas
- `src/pyacli/lib/schemas.py` — input models to expose schemas
- MCP SDK (`mcp` package) — Server, stdio_server, Tool, TextContent

## MCP Tools
- `list_methods()` — list JiraClient public async methods
- `get_method_info(method_name)` — method signature, parameters, docstring
- `get_models(model_name?)` — Pydantic model JSON Schema

## Workflow
1. Implement server.py with 3 tools
2. Implement __init__.py entrypoint
3. Write tests
4. Verify with `poetry run python -m pyacli.mcp`
