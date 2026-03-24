# Allowed Tools

## CLI
- `poetry *` — install, build, run, add, remove
- `acli *` — all acli commands (auth, workitem create/search/view/transition)
- `python *` — run scripts, py_compile, module execution
- `pytest *` — test execution
- `docker *` — build, compose, run
- `git *` — all git operations (push requires confirmation)

## MCP
- `mcp__atlassian__*` — all Atlassian MCP tools (Jira read/write)

## Restrictions (always require user confirmation)
- `poetry publish` — PyPI release
- `docker push` — image registry push
- `git push --force` — force push
