# pyacli 패키지 설계

> 작성일: 2026-03-24
> 상태: v0.1 설계 확정

---

## 1. 목적

Atlassian CLI (`acli`)를 Python async API로 래핑하는 PyPI 패키지.
`subprocess`로 acli를 호출하고, `--json` 출력을 파싱하여 Python 객체로 반환한다.

### 왜 필요한가?

- acli는 터미널 도구 → Python 코드에서 직접 호출하려면 subprocess 보일러플레이트 필요
- 여러 프로젝트에서 Jira 자동화를 쓸 때마다 같은 래핑 코드를 반복 작성하게 됨
- PyPI 패키지로 만들면 `pip install`만으로 재사용 가능

### 첫 소비자

- 회사 내부 Jira 자동화 도구

---

## 2. v0.1 스코프

### 필수 기능

| 기능 | acli 명령어 | Python 메서드 |
|------|------------|--------------|
| 이슈 생성 | `jira workitem create` | `create_issue()` |
| 이슈 검색 | `jira workitem search` | `search_issues()` |
| 이슈 조회 | `jira workitem view` | `get_issue()` |
| 상태 변경 | `jira workitem transition` | `transition_issue()` |

### 공통 요구사항

- async 지원 (`asyncio.create_subprocess_exec`)
- `--json` 출력 파싱 → Pydantic 모델 반환
- 에러 핸들링 (acli 실패 시 예외)
- acli 미설치 감지 + 명확한 에러 메시지

### v0.2+ 확장 후보

- Confluence 지원
- 벌크 생성 (`create-bulk`)
- 댓글 CRUD
- 담당자 변경
- sync/async 둘 다 지원
- 프로젝트 목록 조회

---

## 3. 설계 결정 (2026-03-24 확정)

| 항목 | 결정 | 비고 |
|------|------|------|
| 패키지 이름 | `pyacli` | |
| Python 버전 | 3.11+ | |
| 빌드 도구 | Poetry | |
| 반환 타입 | Pydantic 모델 | 입력도 Pydantic 모델로 받아 유연성 확보 |
| API 설계 | 클래스 기반 + Pydantic 입력 모델 | 파라미터 증가 시 Pydantic Request 모델로 확장 |
| MCP 서버 | 포함 (stdio transport) | 라이브러리 API 문서/스키마 제공용 |

### API 설계 (클래스 기반 + Pydantic)

```python
from pyacli import JiraClient

client = JiraClient(project="WNVO")

# 간단한 호출
issue = await client.create_issue(summary="...", description="...")

# 파라미터가 많을 때 — Pydantic 입력 모델
req = CreateIssueRequest(summary="...", labels=["bug"], custom_fields={...})
issue = await client.create_issue(req)
```

### 에러 처리

- 커스텀 예외 계층 (AcliError → AcliNotFoundError, AcliAuthError, ...)
- acli stderr 파싱해서 구조화된 에러 반환

### 패키지 구조

```
src/
└── pyacli/
    ├── __init__.py
    ├── lib/                  # 라이브러리 (핵심 로직)
    │   ├── __init__.py
    │   ├── client.py         # JiraClient 클래스
    │   ├── models.py         # Pydantic 모델 (입력/출력)
    │   ├── exceptions.py     # 예외 계층
    │   └── runner.py         # subprocess 실행 래퍼
    └── mcp/                  # MCP 서버 (SDK 도우미)
        ├── __init__.py       # python -m pyacli.mcp 엔트리포인트
        └── server.py         # 메서드 목록, 시그니처, 모델 스키마 제공
```

### MCP 서버 (SDK 도우미)

개발자가 pyacli 기반 코드를 작성할 때, Claude가 API 사용법을 안내할 수 있도록 라이브러리 스키마를 제공하는 MCP 서버.

```json
// claude_desktop_config.json — 최초 1회 설정
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
- `list_methods()` — 사용 가능한 메서드 목록
- `get_method_info()` — 메서드 시그니처, 파라미터, 사용 예시
- `get_models()` — Pydantic 모델 스키마 (입력/출력)

### 배포 및 실행 환경

**Docker 이미지** (DockerHub 배포)
- pyacli + acli 바이너리가 포함된 베이스 이미지 제공
- acli 버전은 v0.1에서 특정 버전 고정, 업데이트는 v0.2+에서 고려

```dockerfile
# pyacli 베이스 이미지 (DockerHub: your-org/pyacli:0.1)
FROM python:3.11-slim
RUN curl -LO "https://acli.atlassian.com/linux/latest/acli_linux_amd64/acli" \
    && chmod +x acli && mv acli /usr/local/bin/
RUN pip install pyacli
```

```dockerfile
# 유저 프로젝트에서 사용
FROM your-org/pyacli:0.1
COPY . /app
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
```

**인증**

환경변수 3개로 API 토큰 주입:
- `ATLASSIAN_SITE` — Atlassian 사이트 (예: `your-site.atlassian.net`)
- `ATLASSIAN_EMAIL` — 계정 이메일
- `ATLASSIAN_API_TOKEN` — API 토큰

```yaml
# docker-compose.yml
services:
  app:
    image: your-org/pyacli:0.1
    environment:
      - ATLASSIAN_SITE=your-site.atlassian.net
      - ATLASSIAN_EMAIL=user@example.com
      - ATLASSIAN_API_TOKEN=${ATLASSIAN_API_TOKEN}
```

`runner.py`가 첫 명령 실행 전에 환경변수를 읽어 자동 로그인 처리:

```python
# runner.py 내부 흐름
class AcliRunner:
    async def _ensure_auth(self):
        """환경변수가 있으면 acli 자동 로그인 (이미 로그인 상태면 스킵)"""
        # echo $TOKEN | acli jira auth login --site ... --email ... --token

    async def run(self, *args):
        await self._ensure_auth()
        # acli 명령 실행
```

| 환경 | 로그인 방식 |
|------|------------|
| 로컬 개발 | `acli jira auth login --web` (브라우저) |
| Docker / CI | 환경변수 → `runner.py` 자동 로그인 |

### 테스트 전략

- subprocess mock 기반 단위 테스트 (v0.1)
- acli 실제 호출 E2E 테스트 (v0.2+)

---

## 4. 사용 예시 (목표 API)

```python
from pyacli import JiraClient

# 초기화
client = JiraClient(project="WNVO")

# 이슈 생성
issue = await client.create_issue(
    summary="[Auto] JWT null 체크 누락",
    description="## 에러 원인\nauth.py:45에서 토큰 만료 시 null 체크 누락",
    labels=["auto-detected", "backend"],
)
print(issue.key)  # "WNVO-123"
print(issue.url)  # "https://site.atlassian.net/browse/WNVO-123"

# 이슈 검색
issues = await client.search_issues(
    jql="project = WNVO AND labels = auto-detected",
)

# 이슈 조회
detail = await client.get_issue("WNVO-123")

# 상태 변경
await client.transition_issue("WNVO-123", status="Done")
```

---

## 참고

- [acli 사용 가이드](./acli-usage-guide.md)
