"""
역할 :
- Notion SDK를 통해 Tasks DB에 대한 CRUD/조회(최소기능)를 수행
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from notion_client import Client
from app.core.config import get_settings

class NotionTaskService:
    """
    Notion Tasks 데이터베이스(원천)에 직접 CRUD를 수행하는 얇은 래퍼.
    """

    def __init__(self) -> None:
        settings = get_settings()
        print("="*80)
        print(settings)
        if not settings.notion_token or not settings.notion_tasks_db_id:
            raise RuntimeError(
                "NOTION_TOKEN 또는 NOTION_TASKS_DB_ID가 설정되지 않았습니다. .env를 확인하세요."
            )
        self._db_id = settings.notion_tasks_db_id
        self._client = Client(auth=settings.notion_token)

    # -------- 조회 --------
    def list_tasks(self, page_size: int = 10) -> Dict[str, Any]:
        """
        Tasks 데이터베이스의 최신 항목 일부를 반환합니다.
        - 페이지네이션은 간단히 page_size만 사용(최소 구성).
        """
        resp = self._client.databases.query(
            **{
                "database_id": self._db_id,
                "page_size": page_size,
                # 필요 시 간단한 정렬/필터를 여기에 추가 가능
            }
        )
        return resp

    # -------- 생성 --------
    def create_task(
        self,
        title: str,
        due: Optional[str] = None,
        assignee_ids: Optional[List[str]] = None,  # 현재 DB에 people 속성 없음(무시)
        priority: Optional[str] = None,            # 기존 파라미터 유지: '카테고리'에 매핑
        tags: Optional[List[str]] = None,          # 현재 DB에 multi-select 없음(무시)
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        새 Task 생성(필수: title).
        - 이 워크스페이스의 Tasks DB 실제 속성명에 맞춰 전송:
        - 제목(title)   -> '할 일'
        - 날짜(date)    -> '날짜'
        - 메모(text)    -> '메모'
        - 카테고리(select) -> '카테고리'
        - 현재 DB에는 people('담당자'), multi-select('태그')가 없으므로 전달돼도 무시됩니다.
        - priority 파라미터는 하위 호환을 위해 '카테고리'에 매핑합니다.
        (예: '💪 Work', '❤️ Family', '⚪️ Public' 등 실제 옵션 라벨과 일치해야 함)
        """
        properties: Dict[str, Any] = {
            # 제목은 '할 일' (title)
            "할 일": {"title": [{"text": {"content": title}}]}
        }

        # '날짜' (date)
        if due:
            properties["날짜"] = {"date": {"start": due}}

        # '카테고리' (select)
        # priority를 카테고리로 매핑 (실제 옵션 라벨로 넣어야 함)
        if priority:
            properties["카테고리"] = {"select": {"name": priority}}

        # '메모' (rich_text)
        if notes:
            properties["메모"] = {"rich_text": [{"text": {"content": notes}}]}

        # 현재 DB에는 'Assignee', 'Tags' 속성이 없으므로 무시합니다.

        resp = self._client.pages.create(
            **{
                "parent": {"database_id": self._db_id},
                "properties": properties,
            }
        )
        return resp

    # -------- 업데이트(부분) --------
    def update_task(self, task_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
        """
        Task 속성 부분 업데이트.
        - patch는 Notion 'properties' 구조를 그대로 전달(최소 구성).
        - 이제부터는 한글 속성명을 사용하세요:
        예) {'상태': {'status': {'name': '계획 중'}}}
            {'카테고리': {'select': {'name': '💪 Work'}}}
            {'날짜': {'date': {'start': '2025-10-25'}}}
            {'메모': {'rich_text': [{'text': {'content': '내용'}}]}}
        """
        resp = self._client.pages.update(
            **{
                "page_id": task_id,
                "properties": patch,
            }
        )
        return resp

    # -------- 완료 처리 --------
    def complete_task(self, task_id: str) -> Dict[str, Any]:
        """
        상태(status)를 '완료'로 설정.
        - 실제 DB '상태' 속성의 옵션 이름 중 하나가 '완료'임이 확인됨.
        """
        resp = self._client.pages.update(
            **{
                "page_id": task_id,
                "properties": {"상태": {"status": {"name": "완료"}}},
            }
        )
        return resp

    # -------- 삭제 --------
    def delete_task(self, task_id: str) -> Dict[str, Any]:
        """
        Notion 페이지는 하드 삭제가 아닌 '아카이브' 플래그로 처리됩니다.
        """
        resp = self._client.pages.update(
            **{
                "page_id": task_id,
                "archived": True,
            }
        )
        return resp
    
    # -------- 진단 메서드 --------
    def describe_database(self) -> Dict[str, Any]:
        """
        현재 Tasks DB의 메타(속성 스키마)를 그대로 반환합니다.
        """
        resp = self._client.databases.retrieve(database_id=self._db_id)
        return resp
    
    # -------- 검색/해결 --------
    def find_tasks_by_title(self, title: str, page_size: int = 5) -> Dict[str, Any]:
        """
        '할 일' 제목을 기준으로 Tasks를 검색한다.
        - 우선 equals로 정확 일치 시도, 없으면 contains로 보완한다.
        - 최대 page_size개 반환.
        """
        # 1) equals
        resp_eq = self._client.databases.query(
            **{
                "database_id": self._db_id,
                "page_size": page_size,
                "filter": {
                    "property": "할 일",
                    "title": {"equals": title}
                },
            }
        )
        if resp_eq.get("results"):
            return resp_eq
        # 2) contains
        resp_ct = self._client.databases.query(
            **{
                "database_id": self._db_id,
                "page_size": page_size,
                "filter": {
                    "property": "할 일",
                    "title": {"contains": title}
                },
            }
        )
        return resp_ct
    
    def resolve_task_id(self, ref: str) -> str | None:
        """
        ref가 유효한 Notion page_id(하이픈 포함/미포함 UUID-like)인지 확인하고,
        아니라면 제목 검색으로 page_id를 추출한다.
        - 우선 정확 일치 제목을, 다음으로 contains 결과의 첫 번째를 사용.
        """
        import re

        # UUID-like or 32-hex (하이픈 유무 모두 허용)
        uuid_like = re.compile(r"^[0-9a-fA-F]{32}$|^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
        if uuid_like.match(ref):
            return ref

        # 제목으로 검색
        search = self.find_tasks_by_title(ref, page_size=5)
        results = search.get("results", [])
        if not results:
            return None

        # 정확 일치 우선
        def page_title(p):
            props = p.get("properties", {})
            title_prop = props.get("할 일", {})
            title_items = title_prop.get("title", [])
            return "".join([item.get("plain_text", "") for item in title_items])

        exact = [p for p in results if page_title(p) == ref]
        if exact:
            return exact[0].get("id")

        return results[0].get("id")