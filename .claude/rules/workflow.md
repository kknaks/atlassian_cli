# Workflow Rules

## Implementation order
1. Implement one file
2. Write tests for that file
3. Verify tests pass
4. Move to next file

## Documentation first
- If implementation conflicts with design docs, update docs before writing code
- acli CLI flags must match docs/acli-usage-guide.md

## Code size limits
- Functions: 50 lines max (recommended)
- Files: 300 lines max (recommended)
- No magic numbers — use constants or parameters

## Forbidden
- No `print()` — use `logging` module
- No hardcoded URLs or file paths
