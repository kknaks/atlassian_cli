# /lint

Check code style and type hints.

## Command
```bash
poetry run python -m py_compile src/pyacli/lib/client.py
poetry run python -m py_compile src/pyacli/lib/runner.py
poetry run python -m py_compile src/pyacli/lib/dto.py
poetry run python -m py_compile src/pyacli/lib/schemas.py
poetry run python -m py_compile src/pyacli/lib/exceptions.py
poetry run python -m py_compile src/pyacli/mcp/server.py
```

Verifies all source files compile without syntax errors.
