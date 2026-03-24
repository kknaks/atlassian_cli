# Naming Conventions

- Classes: `PascalCase` (JiraClient, CreateIssueRequest)
- Functions/methods: `snake_case` (create_issue, to_acli_args)
- Constants: `UPPER_SNAKE_CASE` (DEFAULT_TIMEOUT)
- Private members: `_prefix` (_ensure_auth, _exec)
- File names: `snake_case` (dto.py, schemas.py)
- DTO fields: Python `snake_case` + Pydantic `Field(alias="camelCase")` for JSON mapping
