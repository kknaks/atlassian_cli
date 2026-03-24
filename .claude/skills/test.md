# /test

Run pytest for the pyacli project.

## Usage
- `/test` — run all tests
- `/test lib` — run only lib tests
- `/test mcp` — run only mcp tests
- `/test -k name` — run tests matching name

## Command
```bash
poetry run pytest tests/ -v
```

## Options
- `lib` → `poetry run pytest tests/lib/ -v`
- `mcp` → `poetry run pytest tests/mcp/ -v`
- `-k <pattern>` → `poetry run pytest tests/ -v -k "<pattern>"`
