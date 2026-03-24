# Data Layer Separation

## dto.py — Internal data transfer objects
- Converts acli JSON responses to Python objects
- Used internally and as return values
- Config: `extra="ignore"` (ignore unknown fields for acli version compatibility)
- Models: JiraIssue, Status, StatusCategory, IssueType, Priority, User, Project, ParentRef

## schemas.py — External input schemas
- Defines what users pass when calling the library
- Config: `extra="forbid"` (catch typos immediately)
- Models: CreateIssueRequest, SearchIssuesRequest, TransitionIssueRequest
- Each schema has a `to_acli_args()` method to convert to CLI arguments

## Data flow
```
User code              pyacli lib              acli CLI
─────────             ──────────             ──────────
schemas.py     →    client.py      →    subprocess
(input)            to_acli_args()       acli ... --json
                   ←  from_acli()  ←    JSON stdout
                   dto.py
                   (output)
```
