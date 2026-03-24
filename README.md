# pyacli

Python async wrapper for Atlassian CLI (acli). Subprocess로 acli를 호출하고 `--json` 출력을 Pydantic 모델로 반환합니다.

## 설치

```bash
pip install atlassian-acli
```

## 환경변수

```env
ATLASSIAN_SITE=your-site.atlassian.net
ATLASSIAN_EMAIL=user@example.com
ATLASSIAN_API_TOKEN=your-api-token
PYACLI_DEFAULT_PROJECT=WNVO
PYACLI_EPIC_MAP=frontend:WNVO-9,backend:WNVO-23,ai:WNVO-24
```

> acli 바이너리가 필요합니다: `brew tap atlassian/homebrew-acli && brew install acli`

## 사용법

```python
import asyncio
from pyacli import JiraClient

async def main():
    # env에서 자동 로드: PYACLI_DEFAULT_PROJECT, PYACLI_EPIC_MAP
    client = JiraClient()

    # 프로젝트 목록 조회
    projects = await client.list_projects()

    # 에픽 이름으로 이슈 생성 (epic map 사용)
    issue = await client.create_issue(
        summary="로그인 에러 수정",
        epic="frontend",            # → WNVO-9 밑에 생성
        labels=["bug", "backend"],
    )
    print(issue.key)  # WNVO-111
    print(issue.url)  # https://site.atlassian.net/browse/WNVO-111

    # 다른 에픽에 이슈 생성
    await client.create_issue(
        summary="API 에러 처리",
        epic="backend",             # → WNVO-23 밑에 생성
    )

    # 에픽 키를 직접 지정하는 것도 가능 (parent= 우선)
    await client.create_issue(
        summary="특수한 작업",
        parent="WNVO-24",          # 직접 에픽 키 지정
    )

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

    # 등록된 에픽 목록 확인
    print(client.epics)
    # {"frontend": "WNVO-9", "backend": "WNVO-23", "ai": "WNVO-24"}

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

## FastAPI 에러 자동 보고

서버에서 에러 발생 시 자동으로 Jira 버그 이슈를 생성하는 예시:

```python
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pyacli import JiraClient

app = FastAPI()
client = JiraClient()

# ⚠️ @app.exception_handler(Exception) 사용 금지 — ASGI 레벨에서 응답이 깨짐
# ✅ 미들웨어 방식 사용
@app.middleware("http")
async def error_reporting_middleware(request: Request, call_next):
    """에러 발생 시 Jira에 버그 이슈 자동 생성."""
    try:
        return await call_next(request)
    except Exception as exc:
        tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
        description = (
            f"*Endpoint:* {request.method} {request.url.path}\n"
            f"*Error:* {type(exc).__name__}: {exc}\n\n"
            f"{{code}}\n{''.join(tb)}{{code}}"
        )
        try:
            issue = await client.create_issue(
                summary=f"[AUTO-BUG] {type(exc).__name__}: {exc}",
                description=description,
                issue_type="버그",
                epic="backend",
            )
            jira_key = issue.key
        except Exception:
            jira_key = None

        return JSONResponse(
            status_code=500,
            content={"error": str(exc), "jira_issue": jira_key},
        )
```

traceback은 description에 요약을, 상세 로그는 댓글로 분리할 수도 있습니다:

```python
        try:
            issue = await client.create_issue(
                summary=f"[AUTO-BUG] {type(exc).__name__}: {exc}",
                description=f"Endpoint: {request.method} {request.url.path}",
                issue_type="버그",
                epic="backend",
            )
            # 상세 traceback을 댓글로 추가
            await client.add_comment(
                issue.key,
                body=f"{{code}}\n{''.join(tb)}{{code}}",
            )
        except Exception:
            pass
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
      - PYACLI_EPIC_MAP=${PYACLI_EPIC_MAP}
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
