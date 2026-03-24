# pyacli

Python async wrapper for Atlassian CLI (acli). Subprocess로 acli를 호출하고 `--json` 출력을 Pydantic 모델로 반환합니다.

## 설치

```bash
pip install pyacli
```

## 환경변수

```env
ATLASSIAN_SITE=your-site.atlassian.net
ATLASSIAN_EMAIL=user@example.com
ATLASSIAN_API_TOKEN=your-api-token
PYACLI_DEFAULT_PROJECT=PROJ
```

> acli 바이너리가 필요합니다: `brew tap atlassian/homebrew-acli && brew install acli`

## 사용법

```python
import asyncio
from pyacli import JiraClient

async def main():
    client = JiraClient(project="WNVO")

    # 프로젝트 목록 조회
    projects = await client.list_projects()

    # 에픽 밑에 작업 생성
    issue = await client.create_issue(
        summary="로그인 에러 수정",
        issue_type="작업",
        parent="WNVO-9",           # 에픽 키 (필수)
        labels=["bug", "backend"],
    )
    print(issue.key)  # WNVO-111
    print(issue.url)  # https://site.atlassian.net/browse/WNVO-111

    # 작업 밑에 하위작업 생성
    subtask = await client.create_issue(
        summary="UI 구현",
        issue_type="하위 작업",
        parent="WNVO-111",         # 작업 키
    )

    # 이슈 조회
    issue = await client.get_issue("WNVO-111")

    # 에픽의 하위 이슈 검색
    issues = await client.search_issues(
        jql="project = WNVO AND parent = WNVO-9",
    )

    # 상태 변경
    await client.transition_issue("WNVO-111", status="완료")

    # 다른 프로젝트에 이슈 생성 (프로젝트 오버라이드)
    await client.create_issue(
        summary="다른 프로젝트 작업",
        project="OTHER",
        parent="OTHER-1",          # 해당 프로젝트의 에픽
    )

asyncio.run(main())
```

## Jira 계층 구조

```
Project (WNVO)
├── [에픽] 기능구현-프론트 1차          ← parent 없이 생성
│   ├── [작업] 로그인 에러 수정         ← parent = 에픽 키
│   │   ├── [하위작업] UI 구현         ← parent = 작업 키
│   │   └── [하위작업] API 연동
│   └── [작업] 회원가입 구현
└── [에픽] 기능구현-백엔드 1차
```

| 레벨 | 이슈 타입 | parent |
|------|----------|--------|
| 최상위 | 에픽 | 없음 |
| 중간 | 작업 | 에픽 키 |
| 최하위 | 하위 작업 | 작업 키 |

## Pydantic 입력 모델

파라미터가 많을 때 Request 모델을 사용할 수 있습니다:

```python
from pyacli import JiraClient, CreateIssueRequest

client = JiraClient(project="WNVO")

req = CreateIssueRequest(
    summary="복잡한 이슈",
    description="상세 설명",
    type="Bug",
    assignee="user@example.com",
    labels=["bug", "urgent"],
    parent="WNVO-9",
)
issue = await client.create_issue(request=req)
```

## MCP 서버

Claude Desktop/Claude Code에서 pyacli API 사용법을 조회할 수 있는 MCP 서버가 포함되어 있습니다.

```json
{
  "mcpServers": {
    "pyacli": {
      "command": "python",
      "args": ["-m", "pyacli.mcp"]
    }
  }
}
```

제공 도구:
- `list_methods` — JiraClient 메서드 목록
- `get_method_info` — 메서드 시그니처, 파라미터, 설명
- `get_models` — Pydantic 모델 JSON Schema

## Docker

```dockerfile
FROM your-org/pyacli:0.1
COPY . /app
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
```

```yaml
services:
  app:
    image: your-org/pyacli:0.1
    environment:
      - ATLASSIAN_SITE=${ATLASSIAN_SITE}
      - ATLASSIAN_EMAIL=${ATLASSIAN_EMAIL}
      - ATLASSIAN_API_TOKEN=${ATLASSIAN_API_TOKEN}
      - PYACLI_DEFAULT_PROJECT=${PYACLI_DEFAULT_PROJECT}
```

## 인증

| 환경 | 방식 |
|------|------|
| 로컬 개발 | `acli jira auth login --web` (브라우저) |
| Docker / CI | 환경변수 → 자동 로그인 |

## 기술 스택

- Python 3.11+
- Pydantic v2
- MCP SDK
- Poetry
- acli CLI

## 라이선스

MIT
