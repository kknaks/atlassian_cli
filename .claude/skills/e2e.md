# /e2e

Run end-to-end test against real Jira (requires acli auth).

## Command
```bash
poetry run python -c "
import asyncio
from pyacli import JiraClient

async def main():
    client = JiraClient(project='WNVO')
    issue = await client.get_issue('WNVO-110')
    print(f'OK: {issue.key} - {issue.summary}')

asyncio.run(main())
"
```

Verifies the full pipeline: JiraClient → AcliRunner → subprocess → acli → JSON → Pydantic.
