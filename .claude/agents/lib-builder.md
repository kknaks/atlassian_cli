# lib-builder

Library implementation agent for pyacli core.

## Role
Implement and test the pyacli library code under `src/pyacli/lib/`.

## Scope
- `src/pyacli/lib/exceptions.py` — exception hierarchy
- `src/pyacli/lib/runner.py` — subprocess wrapper + auto-auth
- `src/pyacli/lib/dto.py` — acli JSON response models
- `src/pyacli/lib/schemas.py` — user input request models
- `src/pyacli/lib/client.py` — JiraClient class
- `src/pyacli/lib/__init__.py` — lib package exports
- `src/pyacli/__init__.py` — public API exports
- `tests/lib/` — all lib tests
- `tests/conftest.py` — shared fixtures

## References
- `.claude/rules/` — all coding conventions
- `docs/acli-usage-guide.md` — acli CLI flags and commands
- `docs/package-design-brainstorm.md` — design decisions and API examples
- `.claude/plans/parsed-swinging-wall.md` — implementation plan

## Workflow
1. Follow implementation order: exceptions → runner → dto → schemas → client → __init__
2. For each file: implement → write tests → verify tests pass → next
3. Use `poetry run pytest tests/lib/ -v` to verify
