# Typing Rules

- `from __future__ import annotations` in every file
- Type hints required on all function parameters (name + type)
- Return type hints required on all functions
- Use Python 3.11+ syntax: `X | Y` instead of `Union[X, Y]`, `list[str]` instead of `List[str]`
- Avoid `Any` — use only when truly unavoidable (e.g., acli custom fields)
- Pydantic v2 API only: `model_config = ConfigDict(...)`, `Field(alias=...)`
- async/await by default, no sync wrappers
- Docstrings and comments in English
