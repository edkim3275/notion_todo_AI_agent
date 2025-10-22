# notion_todo_AI_agent
사용자 요청에 따라 Notion DB의 TODO List 데이터 조작해주는 AI Agent.

## 프로젝트 구조

### v1

```
/
├── NotionDBLoader.py            # LangChain에서 DB로드(확인/연습용)
├── NotionAPIClass.py       # NotionTodoClient 클래스 (Agent용)
├── NotionTODOAgent.py    # 에이전트 본체 (LLM + Planner + Executor)
```

### v2

```
app/
├── api/
│   └── v1/
│       ├── endpoints/
│       │   └── notion.py         # Notion 관련 REST 엔드포인트
│       └── init.py
├── core/
│   ├── config.py                 # 환경 변수 로드 / Settings
│   ├── time.py                   # 상대 날짜 전처리 유틸
├── data/                         # (로그 등 저장 예정)
├── interface/
│   └── agent.py                  # FastAPI → LangChain Agent 실행 엔트리
├── llm/
│   ├── chains.py                 # Gemini LLM + Tool 기반 에이전트 구성
│   ├── prompts.py                # SYSTEM_PROMPT 정의
│   ├── schemas.py                # Pydantic 모델 정의
│   └── tools.py                  # LangChain Tool 정의 (Notion Task CRUD)
├── services/
│   └── notion_service.py         # Notion API 래퍼 (create/update/delete 등)
├── main.py                       # FastAPI 앱 실행 진입점
├── runserver.py                  # 로컬 실행용 진입 스크립트
└── requirements.txt
```

## 기능개요

- [x]      Notion 연동 |
- [x]      LangChain Agent | Gemini + tools 기반 자연어 명령 처리
- [x]      스마트 툴 | 제목만으로 Task 식별 및 조작
- [x]      상대 날짜 변환 | "내일/모레/어제" → 실제 날짜(YYYY-MM-DD) 자동 변환
- [x]      FastAPI REST API | `v1/notion/tasks/*`
- [ ]      LangGraph적용(설계변경)
- [ ]      Web UI
- [ ]      배포

## 주요 엔드포인트

| 경로                    | 메서드 | 설명                      |
| ----------------------- | ------ | ------------------------- |
| /v1/notion/health       | GET    | 서버 상태 체크            |
| /v1/notion/tasks/create | POST   | Task 생성                 |
| /v1/notion/tasks/list   | GET    | Task 목록 조회            |
| /v1/notion/agent        | POST   | LLM 기반 자연어 명령 수행 |

## 에이전트 예시 요청

### 작업추가

```
curl -s -X POST "http://localhost:8000/v1/notion/agent" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "내일 \"테스트 작업 B\"를 할 일로 추가해줘. 카테고리는 💪 Work, 메모는 \"LLM 경유 생성\""
  }' | jq .
```

### 상태변경

```
curl -s -X POST http://localhost:8000/v1/notion/agent \
  -H "Content-Type: application/json" \
  -d '{
    "text": "\"테스트 작업 A\"를 삭제해줘"
  }' | jq .
```

### 작업삭제

```
curl -X POST http://localhost:8000/v1/notion/agent \
  -H "Content-Type: application/json" \
  -d '{ "text": "\"테스트 작업 B\"를 삭제해줘" }'
```

