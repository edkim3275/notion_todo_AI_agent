import os, requests
from dotenv import load_dotenv
from notion_client import Client
from typing import Any, Dict, List, Optional

# =========================
# Agent‑friendly Notion Todo Client
# =========================
class NotionTodoClient:
    """A thin wrapper around the Notion Python SDK specialized for the TODO DB.
    It exposes clean methods Agent code can call, and an executor for JSON plans
    produced by the planner prompt (intent/create/update/delete/query).
    """
    def __init__(self, notion_client: Client, database_id: str):
        self.notion = notion_client
        self.database_id = database_id.replace("-", "")

    # ---- Utility ----
    @staticmethod
    def _extract_rows(resp: Dict[str, Any]) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for page in resp.get("results", []):
            props = page.get("properties", {})
            title_parts = (props.get("할 일", {}) or {}).get("title", [])
            title = "".join([t.get("plain_text", "") for t in title_parts])
            status = ((props.get("상태") or {}).get("status") or {}).get("name")
            category = ((props.get("카테고리") or {}).get("select") or {}).get("name")
            date = ((props.get("날짜") or {}).get("date") or {}).get("start")
            rows.append({
                "page_id": page.get("id"),
                "title": title,
                "status": status,
                "category": category,
                "date": date,
                "url": page.get("url"),
            })
        return rows

    # ---- Query ----
    def list_tasks(self, *, filter: Optional[Dict[str, Any]] = None, sorts: Optional[List[Dict[str, Any]]] = None, page_size: int = 50) -> List[Dict[str, Any]]:
        payload: Dict[str, Any] = {"page_size": page_size}
        if filter:
            payload["filter"] = filter
        if sorts:
            payload["sorts"] = sorts
        resp = self.notion.databases.query(database_id=self.database_id, **payload)
        return self._extract_rows(resp)

    def find_by_title(self, title: str, *, date_equals: Optional[str] = None, page_size: int = 5) -> List[Dict[str, Any]]:
        and_filters: List[Dict[str, Any]] = [
            {"property": "할 일", "title": {"equals": title}}
        ]
        if date_equals:
            and_filters.append({"property": "날짜", "date": {"equals": date_equals}})
        resp = self.notion.databases.query(
            database_id=self.database_id,
            filter={"and": and_filters},
            page_size=page_size,
        )
        return self._extract_rows(resp)

    # ---- Create ----
    def create_task(self, *, title: str, status: str = "시작 전", date: Optional[str] = None, category: Optional[str] = None, memo: Optional[str] = None) -> Dict[str, Any]:
        props: Dict[str, Any] = {
            "할 일": {"title": [{"type": "text", "text": {"content": title}}]},
            "상태": {"status": {"name": status}},
        }
        if date:
            props["날짜"] = {"date": {"start": date}}
        if category:
            props["카테고리"] = {"select": {"name": category}}
        if memo:
            props["메모"] = {"rich_text": [{"type": "text", "text": {"content": memo}}]}
        return self.notion.pages.create(parent={"database_id": self.database_id}, properties=props)

    # ---- Update/Delete ----
    def update_task(self, page_id: str, *, status: Optional[str] = None, date: Optional[str] = None, memo: Optional[str] = None, category: Optional[str] = None) -> Optional[Dict[str, Any]]:
        props: Dict[str, Any] = {}
        if status is not None:
            props["상태"] = {"status": {"name": status}}
        if date is not None:
            props["날짜"] = {"date": {"start": date}}
        if memo is not None:
            props["메모"] = {"rich_text": [{"type": "text", "text": {"content": memo}}]}
        if category is not None:
            props["카테고리"] = {"select": {"name": category}}
        if not props:
            return None
        return self.notion.pages.update(page_id=page_id, properties=props)

    def archive_task(self, page_id: str) -> Dict[str, Any]:
        return self.notion.pages.update(page_id=page_id, archived=True)

    # ---- Plan executor (runs planner JSON) ----
    def run_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a planner JSON of the shape we defined in NotionAgent prompt.
        Returns a dict with {"ok": bool, "result": Any, "error": Optional[str]}
        """
        try:
            intent = (plan or {}).get("intent")
            request = (plan or {}).get("request", {})
            selection = (plan or {}).get("selection", {})
            body = request.get("body") or {}

            # Resolve selection → page_id when needed
            page_id: Optional[str] = selection.get("page_id")
            if not page_id and selection.get("strategy") in ("by_title_exact", "by_filters", "by_title_fuzzy"):
                title = selection.get("title")
                filters = selection.get("filters") or []
                date_equals: Optional[str] = None
                # try to extract date equals from filters
                for f in filters:
                    if (f.get("property") == "이벤트 날짜" or f.get("property") == "날짜") and (f.get("operator") in ("equals", "on_or_before", "on_or_after")):
                        date_equals = f.get("value")
                if title:
                    candidates = self.find_by_title(title, date_equals=date_equals, page_size=5)
                    if len(candidates) == 1:
                        page_id = candidates[0]["page_id"]
                    elif len(candidates) == 0:
                        return {"ok": False, "error": "no_match", "result": []}
                    else:
                        return {"ok": False, "error": "multiple_matches", "result": candidates}

            if intent == "query":
                # Use body as query body if given; else build from selection.filters
                if not body:
                    and_filters: List[Dict[str, Any]] = []
                    for f in selection.get("filters") or []:
                        prop = f.get("property")
                        op = f.get("operator")
                        val = f.get("value")
                        if prop in ("날짜", "이벤트 날짜"):
                            and_filters.append({"property": prop, "date": {"equals": val}})
                        elif prop in ("카테고리", "상태", "장소"):
                            # select/status handled via equals name
                            key = "status" if prop == "상태" else "select"
                            and_filters.append({"property": prop, key: {"equals": val}})
                        else:
                            and_filters.append({"property": prop, "title": {"contains": val}})
                    body = {"filter": {"and": and_filters}} if and_filters else {}
                resp = self.notion.databases.query(database_id=self.database_id, **body)
                return {"ok": True, "result": self._extract_rows(resp)}

            if intent == "create":
                props = (body or {}).get("properties") or {}
                # Ensure parent database
                result = self.notion.pages.create(parent={"database_id": self.database_id}, properties=props, children=(body or {}).get("children"))
                return {"ok": True, "result": result}

            if intent == "update":
                if not page_id:
                    return {"ok": False, "error": "missing_page_id", "result": None}
                props = (body or {}).get("properties") or {}
                result = self.notion.pages.update(page_id=page_id, properties=props)
                return {"ok": True, "result": result}

            if intent == "delete":
                if not page_id:
                    return {"ok": False, "error": "missing_page_id", "result": None}
                result = self.notion.pages.update(page_id=page_id, archived=True)
                return {"ok": True, "result": result}

            return {"ok": False, "error": f"unknown_intent:{intent}", "result": None}
        except Exception as e:
            return {"ok": False, "error": str(e), "result": None}

# --- Example usage for the Agent (commented) ---
# client = NotionTodoClient(notion, DATABASE_ID)
# plan = {
#   "intent": "update",
#   "request": {"method": "PATCH", "endpoint": "/v1/pages/{page_id}", "body": {"properties": {"상태": {"status": {"name": "완료"}}}}},
#   "selection": {"strategy": "by_title_exact", "title": "Notion Agent 만들기", "filters": []}
# }
# print(client.run_plan(plan))