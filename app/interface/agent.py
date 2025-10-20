"""
app/interface/agent.py

역할:
- 외부에서 '문자열 지시'를 받아 LangChain 에이전트를 실행하는 얇은 엔트리.
- build_agent()는 호출 시마다 새로 생성(개인용/최소 구성). 필요하면 캐시화 가능.
"""

from __future__ import annotations
from app.llm.chains import build_agent
from app.core.config import get_settings
from app.core.time import normalize_korean_relative_dates

def run_agent(user_text: str) -> dict:
    """
    사용자의 자연어 지시를 받아 에이전트를 실행하고, 최종 결과(툴 실행 결과)를 반환한다.
    - 도구는 내부적으로 NotionTaskService를 호출한다.
    - 실패 시 LangChain에서 예외를 발생시킬 수 있으므로, 상위(엔드포인트)에서 처리한다.
    """
    # 사용자의 자연어에서 간단 상대 날짜(오늘/내일/모레/어제)를 절대 날짜로 치환
    settings = get_settings()
    normalized_text = normalize_korean_relative_dates(user_text, settings.tz)
    agent = build_agent()
    # agent.invoke는 {"input": "..."} 형태의 딕셔너리 입력을 받는다.
    result = agent.invoke({"input": normalized_text})
    # result는 {"output": "...", "intermediate_steps": ...} 형태를 포함한다.
    return {"ok": True, "result": result}