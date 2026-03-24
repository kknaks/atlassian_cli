# Atlassian CLI (acli) 사용 가이드

> 작성일: 2026-03-24
> 공식 문서: https://developer.atlassian.com/cloud/acli/guides/introduction/

---

## 1. 설치 (macOS)

### Homebrew (권장)

```bash
brew tap atlassian/homebrew-acli
brew install acli
```

### 직접 설치 (Apple Silicon)

```bash
curl -LO "https://acli.atlassian.com/darwin/latest/acli_darwin_arm64/acli"
chmod +x ./acli
sudo mv ./acli /usr/local/bin/acli
sudo chown root: /usr/local/bin/acli
```

### 설치 확인

```bash
acli --version
```

> 각 CLI 버전은 출시 후 6개월간만 지원. 정기적으로 업데이트 필요.

---

## 2. 인증 (로그인)

### 방법 1: OAuth (브라우저)

```bash
acli jira auth login --web
```

브라우저가 열리고 Atlassian 계정으로 로그인하면 인증 완료.

### 방법 2: API 토큰

토큰 발급: https://id.atlassian.com/manage-profile/security/api-tokens

```bash
# 파일에서 토큰 읽기
acli jira auth login \
  --site "your-site.atlassian.net" \
  --email "your-email@example.com" \
  --token < token.txt

# 직접 입력
echo "<YOUR_API_TOKEN>" | acli jira auth login \
  --site "your-site.atlassian.net" \
  --email "your-email@example.com" \
  --token
```

### 인증 상태 확인

```bash
acli jira auth status
```

### 로그아웃

```bash
acli jira auth logout
```

---

## 3. 프로젝트 조회

```bash
# 전체 목록
acli jira project list --paginate

# 최근 본 프로젝트
acli jira project list --recent

# JSON 출력
acli jira project list --limit 50 --json
```

---

## 4. 이슈 생성 (workitem create)

### 주요 옵션

| 플래그 | 설명 |
|--------|------|
| `-s, --summary` | 이슈 제목 |
| `-p, --project` | 프로젝트 키 |
| `-t, --type` | 이슈 타입 (Task, Epic, Bug 등) |
| `-a, --assignee` | 담당자 (이메일, `@me`, `default`) |
| `-d, --description` | 설명 (일반 텍스트 또는 ADF) |
| `--description-file` | 파일에서 설명 읽기 |
| `-l, --label` | 레이블 (쉼표 구분) |
| `--parent` | 상위 이슈 ID (하위작업 생성 시) |
| `--json` | JSON 형식 출력 |
| `--from-json` | JSON 파일에서 이슈 정의 읽기 |

### 예시

```bash
# 기본 생성
acli jira workitem create \
  --project "PROJ" \
  --type "Task" \
  --summary "로그인 에러 수정"

# 설명 + 담당자 + 레이블
acli jira workitem create \
  --project "PROJ" \
  --type "Task" \
  --summary "[Backend Error] NullPointerException in auth.py" \
  --description "## 에러 원인\nJWT 토큰 만료 시 null 체크 누락" \
  --assignee "user@example.com" \
  --label "bug,backend,auto-detected"

# 파일에서 설명 읽기
acli jira workitem create \
  --project "PROJ" \
  --type "Task" \
  --summary "에러 수정" \
  --description-file "./error_report.txt"

# JSON 파일로 생성
acli jira workitem create --from-json "issue.json"

# JSON 템플릿 생성 (구조 확인용)
acli jira workitem create --generate-json
```

### 벌크 생성

```bash
acli jira workitem create-bulk --from-json "issues.json"
```

---

## 5. 이슈 검색 (workitem search)

### 주요 옵션

| 옵션 | 설명 |
|------|------|
| `--jql` | JQL 쿼리 |
| `--fields` | 표시 필드 (기본: issuetype,key,assignee,priority,status,summary) |
| `--count` | 결과 개수만 표시 |
| `--limit` | 최대 조회 수 |
| `--paginate` | 전체 결과 조회 |
| `--csv` | CSV 출력 |
| `--json` | JSON 출력 |

### 예시

```bash
# 프로젝트 전체 이슈
acli jira workitem search --jql "project = PROJ" --paginate

# 미완료 이슈만
acli jira workitem search --jql "project = PROJ AND status != Done"

# 자동 감지된 에러만
acli jira workitem search --jql "project = PROJ AND labels = auto-detected"

# CSV 내보내기
acli jira workitem search \
  --jql "project = PROJ" \
  --fields "key,summary,assignee,status" \
  --csv
```

---

## 6. 이슈 상태 변경 (workitem transition)

```bash
# 단일 이슈
acli jira workitem transition --key "PROJ-123" --status "Done"

# 여러 이슈
acli jira workitem transition --key "PROJ-123,PROJ-124" --status "In Progress"

# JQL로 일괄 변경
acli jira workitem transition --jql "project = PROJ AND labels = auto-detected" --status "Done"
```

---

## 7. 기타 명령어

```bash
# 이슈 조회
acli jira workitem view --key "PROJ-123"
acli jira workitem view --key "PROJ-123" --json

# 이슈 수정
acli jira workitem edit --key "PROJ-123" --summary "수정된 제목"

# 담당자 변경
acli jira workitem assign --key "PROJ-123" --assignee "user@example.com"

# 이슈 삭제
acli jira workitem delete --key "PROJ-123"

# 댓글 추가
acli jira workitem comment-create --key "PROJ-123" --body "수정 완료"

# 댓글 목록
acli jira workitem comment-list --key "PROJ-123"
```

---

## 8. 명령어 트리

```
acli
├── jira
│   ├── auth
│   │   ├── login         # 로그인 (--web | --token)
│   │   ├── logout        # 로그아웃
│   │   └── status        # 인증 상태
│   ├── project
│   │   └── list          # 프로젝트 목록
│   └── workitem
│       ├── create        # 이슈 생성
│       ├── create-bulk   # 벌크 생성
│       ├── search        # 검색 (JQL)
│       ├── view          # 조회
│       ├── edit          # 수정
│       ├── assign        # 담당자 변경
│       ├── transition    # 상태 변경
│       ├── delete        # 삭제
│       ├── clone         # 복제
│       ├── comment-*     # 댓글 CRUD
│       ├── link          # 이슈 연결
│       └── archive       # 아카이브
└── admin
    └── auth
        ├── login         # 관리자 로그인
        └── status        # 관리자 인증 상태
```

---

## 9. Docker 환경 인증 영속화

```yaml
services:
  worker:
    volumes:
      - acli-auth:/root/.config/acli
volumes:
  acli-auth:
```

최초 셋업: 컨테이너 접속 → `acli jira auth login --web` → 브라우저 인증 → 이후 볼륨으로 영속화.

---

## 참고 링크

- [공식 소개](https://developer.atlassian.com/cloud/acli/guides/introduction/)
- [macOS 설치](https://developer.atlassian.com/cloud/acli/guides/install-macos/)
- [Quick Start](https://developer.atlassian.com/cloud/acli/guides/how-to-get-started/)
- [jira workitem create](https://developer.atlassian.com/cloud/acli/reference/commands/jira-workitem-create/)
- [jira workitem search](https://developer.atlassian.com/cloud/acli/reference/commands/jira-workitem-search/)
- [jira workitem 전체](https://developer.atlassian.com/cloud/acli/reference/commands/jira-workitem/)
