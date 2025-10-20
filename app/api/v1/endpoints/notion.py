"""
역할 :
- Notion/Tasks 관련 API 라우트의 v1 엔드포인트 파일.
- 현재 단계에서는 서버 기동 확인을 위해 간단한 헬스체크 엔드포인트만을 제공
- 2단계에서 실제 CRUD 엔드포인트(예: /tasks/list, /tasks/create ..)를 여기에 추가
"""

from fastapi import APIRouter
from fastapi import Body
from app.services.notion_service import NotionTaskService
from app.llm.schemas import (
    CreateTaskInput,
    UpdateTaskInput,
    CompleteTaskInput,
    DeleteTaskInput,
    ListTasksInput,
)
from fastapi import HTTPException
from app.interface.agent import run_agent

router = APIRouter(prefix="/notion", tags=["notion"])

@router.get("/health")
def notion_health_check() -> dict:
  """
  간단한 헬스체크.
  - 나중에 Notion API 접근성 확인(토큰 연결 여부) 로직을 여기에 추가 할 수 있음
  """
  return {"ok": True, "service": "notion", "stage": 1}

@router.get("/tasks/list")
def list_tasks(page_size: int = 10) -> dict:
    """
    최소 목록 조회(LLM 우회).
    - page_size: 1~100 권장(기본 10)
    """
    svc = NotionTaskService()
    page_size = max(1, min(100, page_size))
    data = svc.list_tasks(page_size=page_size)
    return {"ok": True, "data": data}

@router.post("/tasks/create")
def create_task(payload: CreateTaskInput = Body(...)) -> dict:
    """
    새 Task 생성(필수: title). 그 외 속성은 있으면 반영.
    """
    svc = NotionTaskService()
    data = svc.create_task(
        title=payload.title,
        due=payload.due,
        assignee_ids=payload.assignee_ids,
        priority=payload.priority,
        tags=payload.tags,
        notes=payload.notes,
    )
    return {"ok": True, "data": data}

@router.post("/tasks/update")
def update_task(payload: UpdateTaskInput = Body(...)) -> dict:
    """
    Task 부분 업데이트.
    - payload.patch는 Notion properties 구조를 그대로 전달(최소 구성).
    """
    svc = NotionTaskService()
    data = svc.update_task(task_id=payload.task_id, patch=payload.patch)
    return {"ok": True, "data": data}

@router.post("/tasks/complete")
def complete_task(payload: CompleteTaskInput = Body(...)) -> dict:
    """
    Task 완료 처리(Status='Done' 가정).
    """
    svc = NotionTaskService()
    data = svc.complete_task(task_id=payload.task_id)
    return {"ok": True, "data": data}

@router.post("/tasks/delete")
def delete_task(payload: DeleteTaskInput = Body(...)) -> dict:
    """
    Task 삭제(아카이브). 실수 방지를 위해 confirm=True가 아니면 거부.
    """
    if not payload.confirm:
        return {
            "ok": False,
            "message": "confirm=True가 필요합니다. 실수 방지용 확인 플래그입니다."
        }
    svc = NotionTaskService()
    data = svc.delete_task(task_id=payload.task_id)
    return {"ok": True, "data": data}

@router.get("/db/describe")
def describe_db() -> dict:
    svc = NotionTaskService()
    data = svc.describe_database()
    return {"ok": True, "data": data.get("properties", {})}

@router.post("/agent")
def run_notional_agent(body: dict) -> dict:
    """
    LangChain 에이전트를 통해 '자연어 → 단일 툴 호출 → Notion 반영'을 수행한다.
    - body 예시: {"text": "다음주 금요일에 '건강검진 예약' 추가해줘. 카테고리는 🏥 Health"}
    - 주의: DB 실제 옵션 라벨과 속성명을 사용해야 한다(카테고리 예: '💪 Work').
    """
    text = (body or {}).get("text")
    if not text or not isinstance(text, str):
        raise HTTPException(status_code=422, detail="text(string) 필드가 필요합니다.")
    try:
        resp = run_agent(text)
        return resp
    except Exception as e:
        # 최소 구성: 에러 매핑 없이 메시지만 노출
        raise HTTPException(status_code=500, detail=f"agent error: {e}")