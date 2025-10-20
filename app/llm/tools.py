"""
역할:
- NotionTaskService를 호출하는 LangChain Tools 정의.
- 입력/출력 스키마는 pydantic(BaseModel)로 엄격하게 관리.
- '단일 책임' 원칙: 각 툴은 정확히 한 가지 동작만 수행.

주의:
- DB 실제 속성명(할 일/날짜/메모/카테고리/상태)에 맞춰 서비스가 작성되어 있어야 한다.
"""

from __future__ import annotations
from typing import List, Any, Dict

from langchain_core.tools import tool
from app.services.notion_service import NotionTaskService
from app.llm.schemas import (
    CreateTaskInput,
    UpdateTaskInput,
    CompleteTaskInput,
    DeleteTaskInput,
    ListTasksInput,
    CompleteTaskSmartInput,
    UpdateTaskSmartInput,
    DeleteTaskSmartInput,
    UpdatePropertySmartInput
)
# ---- 목록 조회 ----
@tool(args_schema=ListTasksInput, return_direct=False)
def list_tasks_tool(page_size: int = 10) -> Dict[str, Any]:
    """
    Notion Tasks 목록을 조회한다.
    - page_size: 1~100
    """
    svc = NotionTaskService()
    data = svc.list_tasks(page_size=page_size)
    return {"ok": True, "data": data}

# ---- 생성 ----
@tool(args_schema=CreateTaskInput, return_direct=False)
def create_task_tool(
    title: str,
    due: str | None = None,
    assignee_ids: List[str] | None = None,  # 현재 DB에 people 없음(무시됨)
    priority: str | None = None,            # '카테고리'에 매핑
    tags: List[str] | None = None,          # 현재 DB에 multi-select 없음(무시됨)
    notes: str | None = None,
) -> Dict[str, Any]:
    """
    Task를 생성한다.
    - title은 필수.
    - due는 '날짜' 속성에 반영.
    - priority는 '카테고리(select)'에 반영(실제 옵션 라벨과 일치해야 함).
    - notes는 '메모(rich_text)'에 반영.
    """
    svc = NotionTaskService()
    data = svc.create_task(
        title=title,
        due=due,
        assignee_ids=assignee_ids,
        priority=priority,
        tags=tags,
        notes=notes,
    )
    return {"ok": True, "data": data}

# ---- 업데이트(부분) ----
@tool(args_schema=UpdateTaskInput, return_direct=False)
def update_task_tool(task_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    """
    Task 속성을 부분 업데이트한다.
    - patch는 Notion properties 구조를 그대로 전달(한글 속성명 사용).
    예) {'상태': {'status': {'name': '계획 중'}}}
       {'카테고리': {'select': {'name': '💪 Work'}}}
       {'날짜': {'date': {'start': '2025-10-25'}}}
       {'메모': {'rich_text': [{'text': {'content': '내용'}}]}}
    """
    svc = NotionTaskService()
    data = svc.update_task(task_id=task_id, patch=patch)
    return {"ok": True, "data": data}

# ---- 완료 ----
@tool(args_schema=CompleteTaskInput, return_direct=False)
def complete_task_tool(task_id: str) -> Dict[str, Any]:
    """
    Task를 완료 처리한다(상태='완료').
    """
    svc = NotionTaskService()
    data = svc.complete_task(task_id=task_id)
    return {"ok": True, "data": data}

# ---- 삭제(아카이브) ----
@tool(args_schema=DeleteTaskInput, return_direct=False)
def delete_task_tool(task_id: str, confirm: bool = False) -> Dict[str, Any]:
    """
    Task를 삭제(아카이브)한다.
    - confirm=True가 아니면 거부.
    """
    if not confirm:
        return {"ok": False, "message": "confirm=True 필요"}
    svc = NotionTaskService()
    data = svc.delete_task(task_id=task_id)
    return {"ok": True, "data": data}

@tool(args_schema=CompleteTaskSmartInput, return_direct=False)
def complete_task_smart_tool(task_ref: str) -> Dict[str, Any]:
    """
    제목 또는 page_id로 Task를 완료 처리한다(상태='완료').
    - task_ref가 UUID-like이면 그대로 사용, 아니면 제목 검색으로 page_id를 해석한다.
    """
    svc = NotionTaskService()
    task_id = svc.resolve_task_id(task_ref)
    if not task_id:
        return {"ok": False, "message": f"대상을 찾을 수 없습니다: {task_ref}"}
    data = svc.complete_task(task_id=task_id)
    return {"ok": True, "data": data}

# ---- 스마트 업데이트(제목 또는 ID) ----
@tool(args_schema=UpdateTaskSmartInput, return_direct=False)
def update_task_smart_tool(task_ref: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    """
    제목 또는 page_id로 Task 속성을 부분 업데이트한다.
    - 예) 상태 변경: {"상태": {"status": {"name": "계획 중"}}}
    """
    svc = NotionTaskService()
    task_id = svc.resolve_task_id(task_ref)
    if not task_id:
        return {"ok": False, "message": f"대상을 찾을 수 없습니다: {task_ref}"}
    data = svc.update_task(task_id=task_id, patch=patch)
    return {"ok": True, "data": data}

# ---- 스마트 삭제(제목 또는 ID) ----
@tool(args_schema=DeleteTaskSmartInput, return_direct=False)
def delete_task_smart_tool(task_ref: str, confirm: bool = False) -> Dict[str, Any]:
    """
    제목 또는 page_id로 Task를 삭제(아카이브)한다.
    """
    if not confirm:
        return {"ok": False, "message": "confirm=True 필요"}
    svc = NotionTaskService()
    task_id = svc.resolve_task_id(task_ref)
    if not task_id:
        return {"ok": False, "message": f"대상을 찾을 수 없습니다: {task_ref}"}
    data = svc.delete_task(task_id=task_id)
    return {"ok": True, "data": data}

# ---- 범용 속성 변경 스마트 툴(제목 또는 ID) ----
@tool(args_schema=UpdatePropertySmartInput, return_direct=False)
def update_property_smart_tool(task_ref: str, field: str, value: str) -> Dict[str, Any]:
    """
    제목 또는 page_id로 Task의 '상태/카테고리/날짜/메모' 중 하나를 변경한다.
    - 서버에서 속성별 Notion patch를 자동 구성한다.
      * 상태: {"상태": {"status": {"name": value}}}
      * 카테고리: {"카테고리": {"select": {"name": value}}}
      * 날짜: {"날짜": {"date": {"start": value}}}
      * 메모: {"메모": {"rich_text": [{"text": {"content": value}}]}}
    """
    svc = NotionTaskService()
    task_id = svc.resolve_task_id(task_ref)
    if not task_id:
        return {"ok": False, "message": f"대상을 찾을 수 없습니다: {task_ref}"}

    # 속성별 patch 자동 구성
    if field == "상태":
        patch = {"상태": {"status": {"name": value}}}
    elif field == "카테고리":
        patch = {"카테고리": {"select": {"name": value}}}
    elif field == "날짜":
        patch = {"날짜": {"date": {"start": value}}}
    elif field == "메모":
        patch = {"메모": {"rich_text": [{"text": {"content": value}}]}}
    else:
        return {"ok": False, "message": f"지원하지 않는 속성: {field}"}

    data = svc.update_task(task_id=task_id, patch=patch)
    return {"ok": True, "data": data}

# ---- 에이전트 등록 툴 ----
def get_tools() -> List:
    """
    에이전트에 등록할 툴 모음.
    - '단일 호출' 원칙을 프롬프트에서 강제한다.
    """
    return [
        list_tasks_tool,
        create_task_tool,
        update_task_tool,
        complete_task_tool,
        delete_task_tool,
        complete_task_smart_tool,
        update_task_smart_tool,
        delete_task_smart_tool,
        update_property_smart_tool
    ]