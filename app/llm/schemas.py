"""
역할 :
- LangChain Tool 및 HTTP 요청 바디에 공용으로 사용할 Pydantic 스키마
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

# ---- 공용: 생성 ----
class CreateTaskInput(BaseModel):
    title: str = Field(..., description="Task 제목 -> Notion '할 일' (title)")
    due: Optional[str] = Field(None, description="마감일 -> Notion '날짜'(date), YYYY-MM-DD 또는 ISO")
    assignee_ids: Optional[List[str]] = Field(
        None, description="현재 DB에는 people 없음(무시됨). 추후 '담당자' 속성 추가 시 사용"
    )
    priority: Optional[str] = Field(
        None, description="카테고리(select)에 매핑됨. 예: '💪 Work', '❤️ Family', '⚪️ Public' 등 실제 옵션 라벨"
    )
    tags: Optional[List[str]] = Field(
        None, description="현재 DB에는 multi-select 없음(무시됨). 추후 '태그' 속성 추가 시 사용"
    )
    notes: Optional[str] = Field(None, description="비고 -> Notion '메모'(rich_text)")


# ---- 공용: 업데이트(부분) ----
class UpdateTaskInput(BaseModel):
    task_id: str = Field(..., description="대상 Task의 page_id")
    patch: Dict[str, Any] = Field(
        ..., description="Notion properties patch. 예) {'Status': {'status': {'name': 'Doing'}}}"
    )


# ---- 공용: 완료 ----
class CompleteTaskInput(BaseModel):
    task_id: str = Field(..., description="대상 Task의 page_id")


# ---- 공용: 삭제 ----
class DeleteTaskInput(BaseModel):
    task_id: str = Field(..., description="대상 Task의 page_id")
    confirm: bool = Field(
        False,
        description="실수 방지용 확인 플래그. True일 때만 삭제(아카이브)를 수행.",
    )


# ---- 공용: 목록 조회 ----
class ListTasksInput(BaseModel):
    page_size: int = Field(10, ge=1, le=100, description="페이지당 항목 수(1~100)")

# ---- 스마트/참조 기반: 제목 또는 ID로 대상 지정 ----
class CompleteTaskSmartInput(BaseModel):
    task_ref: str = Field(..., description="page_id 또는 제목 문자열")

class UpdateTaskSmartInput(BaseModel):
    task_ref: str = Field(..., description="page_id 또는 제목 문자열")
    patch: Dict[str, Any] = Field(..., description="Notion properties patch(한글 속성명)")

class DeleteTaskSmartInput(BaseModel):
    task_ref: str = Field(..., description="page_id 또는 제목 문자열")
    confirm: bool = Field(False, description="True일 때만 삭제(아카이브) 수행")

class UpdatePropertySmartInput(BaseModel):
    task_ref: str = Field(..., description="page_id 또는 제목 문자열")
    field: Literal["상태", "카테고리", "날짜", "메모"] = Field(..., description="변경할 속성명(한글)")
    value: str = Field(..., description="설정할 값(상태/카테고리=옵션 라벨, 날짜=YYYY-MM-DD, 메모=텍스트)")