# pyacli — 프로젝트 컨텍스트

## 프로젝트 개요
Atlassian CLI (`acli`)를 Python async API로 래핑하는 PyPI 패키지. subprocess로 acli를 호출하고 `--json` 출력을 파싱하여 Pydantic 모델로 반환한다.

## 현재 상태
v0.1 설계 확정, 구현 시작 단계

## 기술 스택
| 항목 | 결정 |
|------|------|
| 패키지 이름 | `pyacli` |
| Python | 3.11+ |
| 빌드 도구 | Poetry |
| 반환/입력 타입 | Pydantic 모델 |
| API 설계 | 클래스 기반 + Pydantic 입력 모델 |
| MCP 서버 | 포함 (stdio) — 라이브러리 API 스키마 제공 |
| 배포 | Docker 베이스 이미지 (DockerHub) — acli 바이너리 포함 |
| 인증 | 환경변수 (`ATLASSIAN_SITE`, `ATLASSIAN_EMAIL`, `ATLASSIAN_API_TOKEN`) |

## 핵심 문서
| 문서 | 내용 |
|------|------|
| `docs/acli-usage-guide.md` | acli 설치/인증/명령어 가이드 |
| `docs/package-design-brainstorm.md` | v0.1 스코프, 설계 결정, 목표 API |

## 패키지 구조
```
src/pyacli/
├── lib/     # 라이브러리 (client, models, exceptions, runner)
└── mcp/     # MCP 서버 (SDK 도우미 — 메서드/모델 스키마 제공)
```

## v0.1 스코프
- Jira 이슈 생성 (`create_issue`)
- Jira 이슈 검색 (`search_issues`)
- Jira 이슈 조회 (`get_issue`)
- Jira 이슈 상태 변경 (`transition_issue`)
- async 지원 (`asyncio.create_subprocess_exec`)
- MCP 서버 (`python -m pyacli.mcp`)
